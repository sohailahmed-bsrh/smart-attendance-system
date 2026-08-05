import asyncio
import cv2
import json
import os
import subprocess
import sys
import queue
from datetime import datetime

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Import core modules
from attendance_system import recognize_frame, event_queue, get_total_students, emit_event
from config import settings

app = FastAPI(title="Smart Attendance System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# Video Streaming
# ==========================================
camera = None
stream_running = False
camera_lock = asyncio.Lock()

def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(settings.get("camera", 0))
    return camera

async def generate_frames():
    global stream_running
    cam = get_camera()
    stream_running = True
    
    while stream_running:
        success, frame = cam.read()
        if not success:
            await asyncio.sleep(0.1)
            continue
            
        # Process frame
        try:
            annotated_frame, person = recognize_frame(frame)
        except Exception as e:
            print(f"Error in recognition: {e}")
            annotated_frame = frame
            person = None
            
        if person is not None:
            emit_event("recognition", {"person": person})

        # Encode to JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Yield control
        await asyncio.sleep(0.03)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/api/camera/stop")
async def stop_camera():
    global stream_running, camera
    stream_running = False
    if camera is not None:
        camera.release()
        camera = None
    return {"status": "stopped"}

# ==========================================
# SSE Events
# ==========================================
async def event_generator(request: Request):
    """
    Yields events from the queue to the client.
    """
    while True:
        if await request.is_disconnected():
            break
            
        try:
            # Non-blocking get
            event = event_queue.get_nowait()
            yield {
                "event": event["type"],
                "data": json.dumps(event["data"])
            }
        except queue.Empty:
            await asyncio.sleep(0.1)

@app.get("/events")
async def sse_events(request: Request):
    return EventSourceResponse(event_generator(request))

# ==========================================
# API Routes
# ==========================================
import pandas as pd

ATTENDANCE_FILE = "outputs/attendance.csv"
STUDENT_FOLDER = "datasets/students"

@app.get("/api/stats")
def get_stats():
    today_count = 0
    total_records = 0
    if os.path.exists(ATTENDANCE_FILE):
        try:
            df = pd.read_csv(ATTENDANCE_FILE)
            total_records = len(df)
            today = datetime.now().strftime("%Y-%m-%d")
            today_count = int((df["Date"] == today).sum())
        except:
            pass
            
    return {
        "students": get_total_students(),
        "today_attendance": today_count,
        "total_records": total_records
    }

@app.get("/api/attendance/recent")
def get_recent_attendance():
    if not os.path.exists(ATTENDANCE_FILE):
        return []
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
        recent = df.tail(10).to_dict("records")
        recent.reverse()
        return recent
    except:
        return []

@app.post("/api/encode")
def encode_faces_endpoint():
    try:
        subprocess.run([sys.executable, "encode_faces.py"], check=True)
        from attendance_system import reload_embeddings
        reload_embeddings()
        return {"status": "success", "message": "Encoding completed successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/students")
def get_students():
    students = []
    if os.path.exists(STUDENT_FOLDER):
        for name in os.listdir(STUDENT_FOLDER):
            folder = os.path.join(STUDENT_FOLDER, name)
            if os.path.isdir(folder):
                images = len([f for f in os.listdir(folder) if f.endswith(('.jpg', '.jpeg', '.png'))])
                students.append({"name": name, "images": images})
    return students

@app.delete("/api/students/{name}")
def delete_student(name: str):
    folder = os.path.join(STUDENT_FOLDER, name)
    if os.path.exists(folder):
        import shutil
        shutil.rmtree(folder)
        return {"status": "success"}
    return {"status": "error", "message": "Student not found"}

@app.post("/api/students/rename")
def rename_student(old_name: str = Form(...), new_name: str = Form(...)):
    old_folder = os.path.join(STUDENT_FOLDER, old_name)
    new_folder = os.path.join(STUDENT_FOLDER, new_name)
    if os.path.exists(old_folder) and not os.path.exists(new_folder):
        os.rename(old_folder, new_folder)
        return {"status": "success"}
    return {"status": "error", "message": "Invalid names or student already exists"}

@app.post("/api/register/capture")
async def register_capture(name: str = Form(...)):
    """Capture 5 images from current camera feed to register student"""
    cam = get_camera()
    save_folder = os.path.join(STUDENT_FOLDER, name)
    os.makedirs(save_folder, exist_ok=True)
    
    count = 0
    while count < 5:
        success, frame = cam.read()
        if success:
            # Need to flip like the old register_student.py? Let's just save
            cv2.imwrite(os.path.join(save_folder, f"web_{datetime.now().strftime('%H%M%S%f')}.jpg"), frame)
            count += 1
        await asyncio.sleep(0.5)
        
    return {"status": "success", "message": f"Captured 5 images for {name}"}

@app.get("/")
def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)
