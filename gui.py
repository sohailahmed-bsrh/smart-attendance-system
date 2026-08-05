"""
gui.py
======================================================
Smart Attendance System Pro - Main Dashboard
======================================================

Design notes (why it's structured this way):

    - Camera capture and face recognition each run in their own
      background thread, connected by 1-slot queues that always hold
      only the *latest* frame. This means the GUI thread never blocks
      on cv2.VideoCapture.read() or on InsightFace inference, so the
      window never freezes, regardless of camera or model speed.

    - The GUI thread only ever touches Tkinter widgets, and does so
      through app.after() polling loops. This keeps everything on the
      main thread, which is a hard requirement of Tkinter.

    - Camera start/stop is guarded so a VideoCapture is never opened
      twice, and Exit performs a full, ordered shutdown: stop camera
      threads -> release VideoCapture -> cancel all after() jobs ->
      destroy OpenCV windows (defensive) -> destroy the GUI.

    - Registering a student launches register_student.py as a child
      process. The dashboard polls that process without blocking; the
      moment it exits, the dashboard reloads face embeddings and
      refreshes every stat automatically.
"""

import os
import queue
import subprocess
import sys
import threading
from datetime import datetime
from utils import center_window
import cv2
import pandas as pd
from PIL import Image, ImageTk
import customtkinter as ctk

from config import settings
import attendance_system as attendance

# ======================================================
# Theme
# ======================================================

ctk.set_appearance_mode(settings.get("theme", "dark").lower())
ctk.set_default_color_theme("blue")

# ======================================================
# Paths
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_DIR = os.path.join(BASE_DIR, "datasets", "students")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "outputs", "attendance.csv")

CAMERA_POLL_MS = 20      # how often we check for a new processed frame
STATS_REFRESH_MS = 1000  # how often we refresh counts / attendance list
PROCESS_POLL_MS = 300    # how often we check on a child process


# ======================================================
# Threaded Camera Pipeline
# ======================================================

class CameraStream:
    """
    Owns a cv2.VideoCapture and runs capture + recognition on
    background daemon threads. The GUI only ever calls start(),
    stop(), and get_latest_result() from the main thread.
    """

    def __init__(self, camera_index):
        self.camera_index = camera_index
        self.capture = None
        self.capture_thread = None
        self.process_thread = None
        self.running = threading.Event()

        self.raw_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)

    def is_running(self):
        return self.running.is_set()

    def start(self):
        if self.running.is_set():
            return True

        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            self.capture.release()
            self.capture = None
            return False

        self.running.set()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.capture_thread.start()
        self.process_thread.start()
        return True

    def _capture_loop(self):
        while self.running.is_set() and self.capture is not None:
            ret, frame = self.capture.read()
            if not ret:
                continue
            self._replace_in_queue(self.raw_queue, frame)

    def _process_loop(self):
        while self.running.is_set():
            try:
                frame = self.raw_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                processed_frame, person = attendance.recognize_frame(frame)
            except Exception as error:
                print(f"[RECOGNITION ERROR] {error}")
                continue

            self._replace_in_queue(self.result_queue, (processed_frame, person))

    @staticmethod
    def _replace_in_queue(q, item):
        """Keep only the newest item in a maxsize=1 queue."""
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(item)
        except queue.Full:
            pass

    def get_latest_result(self):
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        self.running.clear()

        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.5)
        if self.process_thread is not None:
            self.process_thread.join(timeout=1.5)

        if self.capture is not None:
            self.capture.release()

        self.capture = None
        self.capture_thread = None
        self.process_thread = None

        # Drain queues so a later start() doesn't show a stale frame
        for q in (self.raw_queue, self.result_queue):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass


# ======================================================
# Main Window
# ======================================================

app = ctk.CTk()
app.title("Smart Attendance System Pro")
app.resizable(False, False)
center_window(app, 1366, 768)

camera_stream = CameraStream(settings.get("camera", 0))

# Tracks every app.after() job so Exit can cancel all of them cleanly
_scheduled_jobs = set()

register_process = None
register_in_progress = False


def schedule(delay_ms, callback):
    job_id = app.after(delay_ms, callback)
    _scheduled_jobs.add(job_id)
    return job_id


def cancel_all_scheduled_jobs():
    for job_id in list(_scheduled_jobs):
        try:
            app.after_cancel(job_id)
        except Exception:
            pass
    _scheduled_jobs.clear()


# ======================================================
# Data Helpers
# ======================================================

def total_students():
    return attendance.get_total_students()


def today_attendance_count():
    if not os.path.exists(ATTENDANCE_FILE):
        return 0
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
        today = datetime.now().strftime("%Y-%m-%d")
        return int((df["Date"] == today).sum())
    except Exception:
        return 0


def load_recent_attendance():
    attendance_box.configure(state="normal")
    attendance_box.delete("1.0", "end")

    if not os.path.exists(ATTENDANCE_FILE):
        attendance_box.insert("end", "No attendance records yet.")
        attendance_box.configure(state="disabled")
        return

    try:
        df = pd.read_csv(ATTENDANCE_FILE)
        recent = df.tail(8)

        if recent.empty:
            attendance_box.insert("end", "No attendance records yet.")
        else:
            for _, row in recent.iloc[::-1].iterrows():
                attendance_box.insert("end", f"{row['Name']:<18}{row['Date']}  {row['Time']}\n")

    except Exception as error:
        attendance_box.insert("end", f"Error reading attendance: {error}")

    attendance_box.configure(state="disabled")


# ======================================================
# Layout: Sidebar
# ======================================================

sidebar = ctk.CTkFrame(app, width=210, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar,
    text="🎓 SMART\nATTENDANCE",
    font=("Arial", 18, "bold"),
    justify="center",
).pack(pady=(18, 12))

# ======================================================
# Layout: Content Area
# ======================================================

content = ctk.CTkFrame(app)
content.pack(side="right", fill="both", expand=True)

# ---- Header row: title + live clock side by side ----

header = ctk.CTkFrame(content, fg_color="transparent")
header.pack(fill="x", padx=15, pady=(10, 5))

ctk.CTkLabel(header, text="Dashboard", font=("Arial", 24, "bold")).pack(side="left")

clock_label = ctk.CTkLabel(header, text="", font=("Arial", 14))
clock_label.pack(side="right")


def update_clock():
    clock_label.configure(text=datetime.now().strftime("%d-%b-%Y   |   %I:%M:%S %p"))
    schedule(1000, update_clock)


# ---- Stat cards ----

cards = ctk.CTkFrame(content, fg_color="transparent")
cards.pack(fill="x", padx=15, pady=(0, 8))
cards.grid_columnconfigure((0, 1, 2), weight=1)


def make_card(parent, column, icon_text, initial_value):
    card = ctk.CTkFrame(parent, height=80)
    card.grid(row=0, column=column, padx=6, sticky="ew")
    card.grid_propagate(False)

    ctk.CTkLabel(card, text=icon_text, font=("Arial", 13, "bold")).pack(pady=(10, 2))
    value_label = ctk.CTkLabel(card, text=str(initial_value), font=("Arial", 22, "bold"))
    value_label.pack()
    return value_label


student_count_label = make_card(cards, 0, "👨‍🎓 Students", total_students())
attendance_count_label = make_card(cards, 1, "✅ Today", today_attendance_count())
status_label = make_card(cards, 2, "🟢 Status", "Ready")

# ---- Last recognized student ----

last_frame = ctk.CTkFrame(content)
last_frame.pack(fill="x", padx=15, pady=(0, 8))

ctk.CTkLabel(last_frame, text="👤 Last Recognized Student", font=("Arial", 14, "bold")).pack(
    anchor="w", padx=10, pady=(6, 0)
)
last_student_label = ctk.CTkLabel(last_frame, text="Waiting for recognition...", font=("Arial", 13))
last_student_label.pack(anchor="w", padx=10, pady=(0, 6))

# ---- Middle: camera + right panel ----

middle_frame = ctk.CTkFrame(content, fg_color="transparent")
middle_frame.pack(fill="both", expand=True, padx=15, pady=(0, 8))

camera_frame = ctk.CTkFrame(middle_frame, width=660, height=430)
camera_frame.grid(row=0, column=0, padx=(0, 10), sticky="n")
camera_frame.grid_propagate(False)

ctk.CTkLabel(camera_frame, text="📷 Live Camera", font=("Arial", 15, "bold")).pack(pady=(8, 4))

camera_label = ctk.CTkLabel(camera_frame, text="Camera is Off", width=640, height=360)
camera_label.pack(pady=4)

right_panel = ctk.CTkFrame(middle_frame, width=340)
right_panel.grid(row=0, column=1, sticky="n")
right_panel.grid_propagate(False)

recent_frame = ctk.CTkFrame(right_panel)
recent_frame.pack(fill="x", pady=(0, 8))

ctk.CTkLabel(recent_frame, text="📋 Recent Attendance", font=("Arial", 14, "bold")).pack(pady=(8, 4))

attendance_box = ctk.CTkTextbox(recent_frame, width=310, height=190, font=("Consolas", 12))
attendance_box.pack(padx=8, pady=(0, 8))
attendance_box.configure(state="disabled")

system_frame = ctk.CTkFrame(right_panel)
system_frame.pack(fill="x")

system_info_label = ctk.CTkLabel(system_frame, text="", justify="left", font=("Arial", 12))
system_info_label.pack(padx=10, pady=10, anchor="w")


# ======================================================
# Recurring Refresh Loops
# ======================================================

def poll_camera():
    """Runs every ~20ms. Pulls the newest processed frame, if any."""
    result = camera_stream.get_latest_result()

    if result is not None:
        frame, person = result

        if person is not None:
            last_student_label.configure(text=person)

        display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        display_frame = cv2.resize(display_frame, (640, 360))
        photo = ImageTk.PhotoImage(Image.fromarray(display_frame))

        camera_label.configure(image=photo, text="")
        camera_label.image = photo  # keep a reference

    schedule(CAMERA_POLL_MS, poll_camera)


def refresh_stats():
    """Runs every ~1s. Cheap-ish work (disk reads), so kept infrequent."""
    student_count_label.configure(text=str(total_students()))
    attendance_count_label.configure(text=str(today_attendance_count()))
    load_recent_attendance()
    system_info_label.configure(
        text=(
            f"📅 Date : {datetime.now().strftime('%d-%b-%Y')}\n"
            f"🕒 Time : {datetime.now().strftime('%I:%M:%S %p')}\n"
            f"👨‍🎓 Students : {total_students()}\n"
            f"✅ Today : {today_attendance_count()}"
        )
    )
    schedule(STATS_REFRESH_MS, refresh_stats)


# ======================================================
# Camera Control
# ======================================================

def start_camera():
    if camera_stream.is_running():
        return

    if not camera_stream.start():
        status_label.configure(text="Cam Error", text_color="red")
        return

    status_label.configure(text="Running", text_color="green")
    camera_label.configure(text="")


def stop_camera():
    camera_stream.stop()
    camera_label.configure(image=None, text="Camera Stopped")
    camera_label.image = None
    status_label.configure(text="Stopped", text_color="red")


def start_attendance():
    start_camera()


# ======================================================
# External Tool Launchers
# ======================================================

def launch_tool(script_name):
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, script_name)], cwd=BASE_DIR)


def register_student():
    global register_process, register_in_progress

    if register_in_progress:
        return

    register_in_progress = True
    register_button.configure(state="disabled", text="Registering...")
    status_label.configure(text="Registering", text_color="orange")

    register_process = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "register_student.py")],
        cwd=BASE_DIR,
    )

    schedule(PROCESS_POLL_MS, _watch_register_process)


def _watch_register_process():
    global register_process, register_in_progress

    if register_process is not None and register_process.poll() is None:
        # Still running - check again shortly
        schedule(PROCESS_POLL_MS, _watch_register_process)
        return

    # Registration window closed - refresh everything automatically
    register_process = None
    register_in_progress = False
    register_button.configure(state="normal", text="👤 Register Student")

    attendance.reload_embeddings()
    student_count_label.configure(text=str(total_students()))
    status_label.configure(text="Running" if camera_stream.is_running() else "Ready", text_color="green")


def encode_faces():
    launch_tool("encode_faces.py")
    schedule(1500, lambda: (attendance.reload_embeddings(), student_count_label.configure(text=str(total_students()))))


def view_attendance():
    launch_tool("view_attendance.py")


def export_excel():
    launch_tool("export_excel.py")


def open_analytics():
    launch_tool("analytics.py")


def open_student_manager():
    launch_tool("student_manager.py")


def open_settings():
    launch_tool("settings.py")


# ======================================================
# Safe Exit
# ======================================================

def exit_application():
    """Full, ordered shutdown so no camera/thread/window is left dangling."""
    cancel_all_scheduled_jobs()
    camera_stream.stop()

    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    app.quit()
    app.destroy()


# ======================================================
# Sidebar Buttons
# ======================================================

def sidebar_button(text, command, danger=False):
    return ctk.CTkButton(
        sidebar,
        text=text,
        width=185,
        height=36,
        command=command,
        fg_color="red" if danger else None,
        hover_color="darkred" if danger else None,
    )


sidebar_button("▶ Start Attendance", start_attendance).pack(pady=4)
register_button = sidebar_button("👤 Register Student", register_student)
register_button.pack(pady=4)
sidebar_button("🔄 Encode Faces", encode_faces).pack(pady=4)
sidebar_button("📋 View Attendance", view_attendance).pack(pady=4)
sidebar_button("📊 Analytics", open_analytics).pack(pady=4)
sidebar_button("👨‍🎓 Student Manager", open_student_manager).pack(pady=4)
sidebar_button("⚙ Settings", open_settings).pack(pady=4)
sidebar_button("📤 Export Excel", export_excel).pack(pady=4)
sidebar_button("⏹ Stop Camera", stop_camera).pack(pady=4)
sidebar_button("❌ Exit", exit_application, danger=True).pack(pady=(14, 4))

ctk.CTkLabel(sidebar, text="Developed By\nSohail Ahmed", font=("Arial", 11)).pack(side="bottom", pady=12)

# ======================================================
# Window Close (titlebar X) - same safe path as Exit button
# ======================================================

app.protocol("WM_DELETE_WINDOW", exit_application)

# ======================================================
# Kick off recurring loops and run
# ======================================================

load_recent_attendance()
update_clock()
refresh_stats()
poll_camera()

app.mainloop()
