"""
register_student.py
======================================================
Smart Attendance System Pro - Student Registration
======================================================

Runs as its own process (launched from gui.py). Deliberately does NOT
import attendance_system, so it never has to load the InsightFace
model just to capture a few photos - it stays fast and lightweight.

Flow:
    Enter name -> Start Camera -> Capture Images -> Finish Registration
        -> encode_faces.py runs in a background thread (GUI stays responsive)
        -> success/failure message shown
        -> window closes automatically

The parent dashboard (gui.py) detects this process exiting and takes
care of reloading embeddings and refreshing the dashboard - no extra
signaling needed from this file.
"""

import os
import sys
import subprocess
import threading
from tkinter import messagebox
from utils import center_window
import cv2
from PIL import Image, ImageTk
import customtkinter as ctk

from config import settings

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
ENCODE_SCRIPT = os.path.join(BASE_DIR, "encode_faces.py")

CAMERA_POLL_MS = 20

# ======================================================
# Lightweight Voice (own thread, own engine - independent of gui.py)
# ======================================================

import queue  # noqa: E402
import pyttsx3  # noqa: E402

_voice_queue = queue.Queue()
_voice_thread = None
_voice_thread_lock = threading.Lock()


def _voice_worker():
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)
    except Exception as error:
        print(f"[VOICE ERROR] {error}")
        return

    while True:
        text = _voice_queue.get()
        if text is None:
            break
        try:
            if settings.get("voice", True):
                engine.say(text)
                engine.runAndWait()
        except Exception as error:
            print(f"[VOICE ERROR] {error}")
        finally:
            _voice_queue.task_done()


def speak(text):
    global _voice_thread
    with _voice_thread_lock:
        if _voice_thread is None or not _voice_thread.is_alive():
            _voice_thread = threading.Thread(target=_voice_worker, daemon=True)
            _voice_thread.start()
    _voice_queue.put(text)


# ======================================================
# Threaded Camera Preview (capture-only, no recognition)
# ======================================================

class PreviewCamera:
    def __init__(self, camera_index):
        self.camera_index = camera_index
        self.capture = None
        self.thread = None
        self.running = threading.Event()

        self._frame_lock = threading.Lock()
        self._latest_frame = None

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
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def _loop(self):
        while self.running.is_set() and self.capture is not None:
            ret, frame = self.capture.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            with self._frame_lock:
                self._latest_frame = frame

    def get_latest_frame(self):
        with self._frame_lock:
            return None if self._latest_frame is None else self._latest_frame.copy()

    def stop(self):
        self.running.clear()
        if self.thread is not None:
            self.thread.join(timeout=1.5)
        if self.capture is not None:
            self.capture.release()
        self.capture = None
        self.thread = None
        with self._frame_lock:
            self._latest_frame = None


# ======================================================
# Window
# ======================================================

app = ctk.CTk()
app.title("Register Student")
app.resizable(False, False)
center_window(app, 950, 700)

preview_camera = PreviewCamera(settings.get("camera", 0))

image_count = 0
save_folder = ""
finishing = False  # guards against double-clicks during encoding

_scheduled_jobs = set()


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
# Header
# ======================================================

ctk.CTkLabel(app, text="👤 Register Student", font=("Arial", 24, "bold")).pack(pady=(16, 8))

name_frame = ctk.CTkFrame(app, fg_color="transparent")
name_frame.pack(pady=4)

ctk.CTkLabel(name_frame, text="Student Name", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=8)
name_entry = ctk.CTkEntry(name_frame, width=300, font=("Arial", 14))
name_entry.grid(row=0, column=1, padx=8)

camera_label = ctk.CTkLabel(app, text="Camera is Off", width=680, height=400)
camera_label.pack(pady=10)

counter_label = ctk.CTkLabel(app, text="Captured Images : 0", font=("Arial", 15, "bold"))
counter_label.pack()


# ======================================================
# Camera Control
# ======================================================

def start_camera():
    if preview_camera.is_running():
        return

    if not preview_camera.start():
        messagebox.showerror("Camera Error", "Unable to open camera.")
        return

    camera_label.configure(text="")
    poll_camera()


def poll_camera():
    if not preview_camera.is_running():
        return

    frame = preview_camera.get_latest_frame()
    if frame is not None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (680, 400))
        photo = ImageTk.PhotoImage(Image.fromarray(rgb))
        camera_label.configure(image=photo, text="")
        camera_label.image = photo

    schedule(CAMERA_POLL_MS, poll_camera)


def stop_camera_preview():
    preview_camera.stop()
    camera_label.configure(image=None, text="Camera Closed")
    camera_label.image = None


# ======================================================
# Capture Image
# ======================================================

def capture_image():
    global image_count, save_folder

    if not preview_camera.is_running():
        messagebox.showerror("Error", "Start the camera first.")
        return

    student_name = name_entry.get().strip()
    if student_name == "":
        messagebox.showerror("Error", "Please enter the student name.")
        return

    frame = preview_camera.get_latest_frame()
    if frame is None:
        messagebox.showerror("Error", "No camera frame available yet. Try again.")
        return

    save_folder = os.path.join(STUDENTS_DIR, student_name)
    os.makedirs(save_folder, exist_ok=True)

    image_count += 1
    filename = os.path.join(save_folder, f"{image_count}.jpg")

    try:
        cv2.imwrite(filename, frame)
    except Exception as error:
        image_count -= 1
        messagebox.showerror("Error", f"Could not save image:\n{error}")
        return

    counter_label.configure(text=f"Captured Images : {image_count}")


# ======================================================
# Finish Registration
# ======================================================

def finish_registration():
    global finishing

    if finishing:
        return

    student_name = name_entry.get().strip()
    if student_name == "":
        messagebox.showerror("Error", "Please enter the student name.")
        return

    if image_count == 0:
        messagebox.showwarning("Warning", "Capture at least one image before finishing.")
        return

    finishing = True
    finish_button.configure(state="disabled", text="Encoding...")
    capture_button.configure(state="disabled")
    start_button.configure(state="disabled")

    stop_camera_preview()

    # Run encode_faces.py off the GUI thread so the window never freezes
    result_holder = {}

    def run_encoding():
        try:
            subprocess.run([sys.executable, ENCODE_SCRIPT], cwd=BASE_DIR, check=True)
            result_holder["ok"] = True
        except subprocess.CalledProcessError as error:
            result_holder["ok"] = False
            result_holder["error"] = f"encode_faces.py exited with an error (code {error.returncode})."
        except Exception as error:
            result_holder["ok"] = False
            result_holder["error"] = str(error)

    encoding_thread = threading.Thread(target=run_encoding, daemon=True)
    encoding_thread.start()

    check_encoding_done(encoding_thread, result_holder)


def check_encoding_done(encoding_thread, result_holder):
    if encoding_thread.is_alive():
        schedule(200, lambda: check_encoding_done(encoding_thread, result_holder))
        return

    if result_holder.get("ok"):
        speak("Congratulations. Student registration completed successfully.")
        messagebox.showinfo(
            "Success",
            "Student registered successfully!\n\nFace encoding completed.",
        )
    else:
        messagebox.showerror(
            "Encoding Failed",
            f"Registration saved, but face encoding failed:\n\n{result_holder.get('error', 'Unknown error')}",
        )

    close_window()


# ======================================================
# Close Window
# ======================================================

def close_window():
    cancel_all_scheduled_jobs()
    preview_camera.stop()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", close_window)

# ======================================================
# Buttons
# ======================================================

button_frame = ctk.CTkFrame(app, fg_color="transparent")
button_frame.pack(pady=18)

start_button = ctk.CTkButton(button_frame, text="📷 Start Camera", width=170, command=start_camera)
start_button.grid(row=0, column=0, padx=8)

capture_button = ctk.CTkButton(button_frame, text="📸 Capture Image", width=170, command=capture_image)
capture_button.grid(row=0, column=1, padx=8)

finish_button = ctk.CTkButton(button_frame, text="✅ Finish Registration", width=190, command=finish_registration)
finish_button.grid(row=0, column=2, padx=8)

app.mainloop()
