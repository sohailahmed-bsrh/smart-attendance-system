// main.js

document.addEventListener('DOMContentLoaded', () => {
    startClock();
    fetchStats();
    fetchRecentAttendance();
    setupSSE();
});

// --- Tab Navigation ---
function showTab(tabId) {
    // Update active button
    document.querySelectorAll('.menu-btn').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Update active tab
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');

    // Update Page Title
    const titles = {
        'dashboard': 'Dashboard',
        'students': 'Student Manager',
        'register': 'Register Student',
        'settings': 'System Settings'
    };
    document.getElementById('pageTitle').innerText = titles[tabId];

    if (tabId === 'students') {
        loadStudents();
    }
}

// --- Clock ---
function startClock() {
    setInterval(() => {
        const now = new Date();
        document.getElementById('liveClock').innerText = now.toLocaleTimeString() + ' | ' + now.toLocaleDateString();
    }, 1000);
}

// --- Dashboard API Calls ---
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('statTotalStudents').innerText = data.students;
        document.getElementById('statToday').innerText = data.today_attendance;
        document.getElementById('statTotalRecords').innerText = data.total_records;
    } catch (e) {
        console.error("Failed to fetch stats", e);
    }
}

async function fetchRecentAttendance() {
    try {
        const res = await fetch('/api/attendance/recent');
        const data = await res.json();
        const list = document.getElementById('recentAttendanceList');
        list.innerHTML = '';
        
        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'attendance-item';
            div.innerHTML = `
                <span class="att-name">${item.Name}</span>
                <span class="att-time">${item.Time}</span>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        console.error("Failed to fetch recent attendance", e);
    }
}

// --- Real-time Events (SSE) ---
function setupSSE() {
    const evtSource = new EventSource("/events");
    
    evtSource.addEventListener("recognition", function(e) {
        const data = JSON.parse(e.data);
        document.getElementById('lastRecognizedName').innerText = data.person;
    });

    evtSource.addEventListener("attendance_updated", function(e) {
        fetchStats();
        fetchRecentAttendance();
    });

    evtSource.addEventListener("voice", function(e) {
        const data = JSON.parse(e.data);
        // Play highly natural browser TTS
        if(document.getElementById('setVoice').value === 'true') {
            const msg = new SpeechSynthesisUtterance();
            msg.text = data;
            // Select a good english voice if available
            const voices = window.speechSynthesis.getVoices();
            const premiumVoice = voices.find(v => v.name.includes("Google") || v.name.includes("Microsoft Zira") || v.lang === 'en-US');
            if (premiumVoice) msg.voice = premiumVoice;
            msg.rate = 1.0;
            msg.pitch = 1.1;
            window.speechSynthesis.speak(msg);
        }
    });
}

// --- Student Manager ---
async function loadStudents() {
    try {
        const res = await fetch('/api/students');
        const students = await res.json();
        const tbody = document.getElementById('studentTableBody');
        tbody.innerHTML = '';
        
        students.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${s.name}</strong></td>
                <td>${s.images}</td>
                <td class="actions">
                    <button class="btn-danger small-btn" onclick="deleteStudent('${s.name}')"><i class="fa-solid fa-trash"></i> Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load students", e);
    }
}

async function deleteStudent(name) {
    if(confirm(`Are you sure you want to delete ${name}?`)) {
        await fetch(`/api/students/${name}`, { method: 'DELETE' });
        loadStudents();
        fetchStats();
    }
}

async function encodeFaces() {
    if(!confirm("This might take a few moments. Continue?")) return;
    
    try {
        const res = await fetch('/api/encode', { method: 'POST' });
        const data = await res.json();
        if(data.status === 'success') {
            alert("Model retrained successfully!");
            fetchStats();
        } else {
            alert("Error: " + data.message);
        }
    } catch (e) {
        alert("Request failed.");
    }
}

// --- Registration ---
async function registerStudent() {
    const name = document.getElementById('regStudentName').value.trim();
    if(!name) {
        alert("Please enter a name");
        return;
    }
    
    const btn = document.getElementById('btnCapture');
    const status = document.getElementById('regStatus');
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Capturing... Please look at the camera';
    status.innerText = "";
    
    try {
        const formData = new FormData();
        formData.append("name", name);
        
        const res = await fetch('/api/register/capture', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            status.innerText = "Images captured successfully! Now training the model...";
            await fetch('/api/encode', { method: 'POST' });
            status.innerText = `Registration complete for ${name}!`;
            document.getElementById('regStudentName').value = '';
            fetchStats();
        } else {
            status.innerText = "Error: " + data.message;
            status.style.color = 'red';
        }
    } catch (e) {
        status.innerText = "Failed to capture.";
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-camera-retro"></i> Capture Images';
    }
}

// --- Camera Control ---
document.getElementById('stopCameraBtn').addEventListener('click', async () => {
    await fetch('/api/camera/stop', { method: 'POST' });
    document.getElementById('videoStream').src = '';
    document.getElementById('videoStream').alt = 'Camera Stopped';
    alert("Camera stopped. Restart the backend to resume.");
});

// Ensure voices are loaded for Safari/Chrome bug
window.speechSynthesis.onvoiceschanged = function() {
    window.speechSynthesis.getVoices();
};
