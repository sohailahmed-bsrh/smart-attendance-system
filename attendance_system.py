"""
attendance_system.py
======================================================
Smart Attendance System Pro
Core Face Recognition & Attendance Engine
======================================================

Responsibilities:
    - Load / reload the InsightFace recognition model and embeddings
    - Recognize faces in a frame and draw overlays
    - Mark attendance once per student per day (thread-safe)
    - Save unknown faces (rate limited)
    - Announce voice messages from a single background worker thread
      so speech never overlaps and never blocks the caller (GUI)

This module is imported by gui.py (for live recognition) and can also
be run directly for a quick console/OpenCV test of the pipeline.
"""

import os
import pickle
import queue
import threading
from datetime import datetime

import cv2
import numpy as np
import pandas as pd

from config import settings

# ======================================================
# Paths
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
EMBEDDINGS_FILE = os.path.join(MODELS_DIR, "face_embeddings.pkl")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
ATTENDANCE_FILE = os.path.join(OUTPUTS_DIR, "attendance.csv")
UNKNOWN_FOLDER = os.path.join(OUTPUTS_DIR, "unknown_faces")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(UNKNOWN_FOLDER, exist_ok=True)

# ======================================================
# Configuration
# ======================================================

RECOGNITION_THRESHOLD = float(settings.get("threshold", 0.5))
UNKNOWN_SAVE_INTERVAL_SECONDS = 10
EMBEDDING_SIZE = 512

# ======================================================
# Face Recognition Model (loaded once, process-wide)
# ======================================================

from insightface.app import FaceAnalysis  # noqa: E402

_face_app = FaceAnalysis(name="buffalo_l")
_face_app.prepare(ctx_id=-1, det_size=(640, 640))

# ======================================================
# Thread-safe Embedding Store
# ======================================================

_embeddings_lock = threading.RLock()
known_embeddings = np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
known_names = []


def _normalize_rows(vectors):
    """L2-normalize each row of a matrix, guarding against zero norms."""
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.size == 0:
        return vectors.reshape(0, EMBEDDING_SIZE)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _load_embeddings_from_disk():
    """Read the embeddings pickle file. Returns (embeddings, names)."""
    if not os.path.exists(EMBEDDINGS_FILE):
        return np.empty((0, EMBEDDING_SIZE), dtype=np.float32), []

    try:
        with open(EMBEDDINGS_FILE, "rb") as f:
            data = pickle.load(f)

        raw_embeddings = data.get("embeddings", [])
        names = list(data.get("names", []))
        embeddings = _normalize_rows(raw_embeddings)
        return embeddings, names

    except Exception as error:
        print(f"[EMBEDDINGS ERROR] Failed to load embeddings: {error}")
        return np.empty((0, EMBEDDING_SIZE), dtype=np.float32), []


def reload_embeddings():
    """
    Reload known face embeddings from disk into memory.
    Thread-safe. Call this after registering a new student and
    re-running encode_faces.py.
    """
    global known_embeddings, known_names

    embeddings, names = _load_embeddings_from_disk()

    with _embeddings_lock:
        known_embeddings = embeddings
        known_names = names

    print(f"[INFO] Embeddings reloaded successfully ({len(set(known_names))} students).")


def get_total_students():
    """Return the number of unique enrolled students."""
    with _embeddings_lock:
        return len(set(known_names))


# Load embeddings once at import time
reload_embeddings()

from voice_engine import speak


# ======================================================
# Attendance Marking
# ======================================================

_attendance_lock = threading.RLock()
_spoken_names_today = set()


def _read_attendance_dataframe():
    if os.path.exists(ATTENDANCE_FILE):
        try:
            return pd.read_csv(ATTENDANCE_FILE)
        except Exception as error:
            print(f"[ATTENDANCE ERROR] Could not read attendance file: {error}")

    return pd.DataFrame(columns=["Name", "Date", "Time"])


def mark_attendance(name):
    """
    Mark attendance for `name` if not already marked today.

    Returns:
        "marked"          - attendance recorded for the first time today
        "already_marked"  - attendance was already recorded today
    """
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    with _attendance_lock:
        df = _read_attendance_dataframe()

        already_marked = ((df["Name"] == name) & (df["Date"] == today)).any()

        if already_marked:
            if name not in _spoken_names_today:
                _spoken_names_today.add(name)
                speak(f"Welcome back {name}. Your attendance has already been marked today.")
            return "already_marked"

        df.loc[len(df)] = [name, today, now_time]

        try:
            df.to_csv(ATTENDANCE_FILE, index=False)
        except Exception as error:
            print(f"[ATTENDANCE ERROR] Could not write attendance file: {error}")
            return "already_marked"

        if name not in _spoken_names_today:
            _spoken_names_today.add(name)
            speak(f"Welcome {name}. Your attendance has been marked successfully. Have a great day.")

        print(f"[ATTENDANCE] {name} marked at {now_time}")
        return "marked"


def reset_voice_cache():
    """Clear the set of names already announced (e.g. at midnight rollover)."""
    with _attendance_lock:
        _spoken_names_today.clear()


# Kept for backward compatibility with older callers
def reset_daily_attendance():
    reset_voice_cache()


def reset_voice():
    reset_voice_cache()


# ======================================================
# Unknown Face Saving (rate limited)
# ======================================================

_unknown_lock = threading.Lock()
_last_unknown_saved_at = None


def save_unknown(frame):
    """Save a snapshot of an unrecognized face, at most once every 10s."""
    global _last_unknown_saved_at

    with _unknown_lock:
        now = datetime.now()

        if (
            _last_unknown_saved_at is not None
            and (now - _last_unknown_saved_at).total_seconds() < UNKNOWN_SAVE_INTERVAL_SECONDS
        ):
            return

        filename = now.strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
        filepath = os.path.join(UNKNOWN_FOLDER, filename)

        try:
            cv2.imwrite(filepath, frame)
            _last_unknown_saved_at = now
        except Exception as error:
            print(f"[UNKNOWN FACE ERROR] {error}")


# ======================================================
# Face Recognition
# ======================================================

def recognize_frame(frame):
    """
    Run face detection + recognition on a single BGR frame.

    Draws bounding boxes / labels directly onto the frame and marks
    attendance for any recognized student.

    Returns:
        (annotated_frame, recognized_person_or_None)
    """
    recognized_person = None

    with _embeddings_lock:
        embeddings_snapshot = known_embeddings
        names_snapshot = list(known_names)

    try:
        faces = _face_app.get(frame)
    except Exception as error:
        print(f"[RECOGNITION ERROR] {error}")
        faces = []

    for face in faces:
        embedding = face.embedding.astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm == 0:
            continue
        embedding = embedding / norm

        x1, y1, x2, y2 = map(int, face.bbox)

        best_score = -1.0
        best_index = -1

        if len(embeddings_snapshot) > 0:
            similarities = np.dot(embeddings_snapshot, embedding)
            best_index = int(np.argmax(similarities))
            best_score = float(similarities[best_index])

        if best_index >= 0 and best_score >= RECOGNITION_THRESHOLD:
            name = names_snapshot[best_index]
            color = (0, 255, 0)
            label = f"{name}  {best_score:.2f}"

            mark_attendance(name)
            recognized_person = name

        else:
            name = "Unknown"
            color = (0, 0, 255)
            label = f"Unknown  {best_score:.2f}"
            save_unknown(frame)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

    timestamp_text = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cv2.putText(
        frame,
        timestamp_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2,
    )

    return frame, recognized_person


# ======================================================
# Test Mode (run this file directly to sanity-check the pipeline)
# ======================================================

if __name__ == "__main__":
    test_camera_index = settings.get("camera", 0)
    cap = cv2.VideoCapture(test_camera_index)

    if not cap.isOpened():
        print("Camera Error")
    else:
        print("Press 'q' to quit test mode.")
        while True:
            ret, test_frame = cap.read()
            if not ret:
                break

            test_frame, person = recognize_frame(test_frame)
            cv2.imshow("Smart Attendance System - Test Mode", test_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
