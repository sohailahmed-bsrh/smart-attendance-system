import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from src.utils.helpers import BASE_DIR, get_timestamp
from src.utils.config import config
from src.core.database import mark_attendance
from src.core.voice_engine import voice
import time

class FaceEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance
        
    def _init_engine(self):
        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self.known_embeddings = {}
        self.last_unknown_save = 0
        self._spoken_names_today = set()
        self.reload_embeddings()

    def reload_embeddings(self):
        self.known_embeddings = {}
        students_dir = os.path.join(BASE_DIR, "datasets", "students")
        if not os.path.exists(students_dir):
            return
            
        for name in os.listdir(students_dir):
            folder = os.path.join(students_dir, name)
            if not os.path.isdir(folder):
                continue
                
            emb_list = []
            for img_name in os.listdir(folder):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img_path = os.path.join(folder, img_name)
                    img = cv2.imread(img_path)
                    if img is not None:
                        faces = self.app.get(img)
                        if faces:
                            emb_list.append(faces[0].normed_embedding)
            if emb_list:
                self.known_embeddings[name] = np.mean(emb_list, axis=0)

    def _save_unknown_face(self, img, bbox):
        if not config.get("save_unknown_faces"):
            return
            
        current_time = time.time()
        # Save max once every 10 seconds
        if current_time - self.last_unknown_save < 10:
            return
            
        x1, y1, x2, y2 = map(int, bbox)
        # Add padding
        h, w = img.shape[:2]
        x1 = max(0, x1 - 20)
        y1 = max(0, y1 - 20)
        x2 = min(w, x2 + 20)
        y2 = min(h, y2 + 20)
        
        face_crop = img[y1:y2, x1:x2]
        if face_crop.size == 0:
            return
            
        unknown_dir = os.path.join(BASE_DIR, "outputs", "unknown_faces")
        os.makedirs(unknown_dir, exist_ok=True)
        filepath = os.path.join(unknown_dir, f"unknown_{get_timestamp()}.jpg")
        cv2.imwrite(filepath, face_crop)
        self.last_unknown_save = current_time

    def process_frame(self, frame):
        """Processes a frame, draws bboxes, marks attendance, returns annotated frame."""
        faces = self.app.get(frame)
        threshold = config.get("recognition_threshold") / 100.0 # Convert 25.0 to 0.25

        for face in faces:
            bbox = face.bbox.astype(int)
            emb = face.normed_embedding

            best_match = None
            best_sim = -1

            for name, known_emb in self.known_embeddings.items():
                sim = np.dot(emb, known_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_match = name

            is_known = best_match and best_sim >= threshold
            
            if is_known:
                color = (0, 255, 0) # Green
                label = f"{best_match} ({best_sim*100:.1f}%)"
                
                # Mark attendance logic
                status = mark_attendance(best_match)
                if status == "marked" and best_match not in self._spoken_names_today:
                    self._spoken_names_today.add(best_match)
                    voice.speak(f"Welcome {best_match}. Attendance marked successfully.")
                elif status == "already_marked" and best_match not in self._spoken_names_today:
                    self._spoken_names_today.add(best_match)
                    voice.speak(f"Welcome back {best_match}. Attendance already marked today.")
            else:
                color = (0, 0, 255) # Red
                label = "Unknown"
                self._save_unknown_face(frame, bbox)

            # Professional UI for bounding box
            # Draw semi-transparent background for text
            overlay = frame.copy()
            cv2.rectangle(overlay, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.6, 1)
            cv2.rectangle(overlay, (bbox[0], bbox[1] - h - 10), (bbox[0] + w + 10, bbox[1]), color, -1)
            
            # Blend overlay for modern look
            alpha = 0.8
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            cv2.putText(frame, label, (bbox[0] + 5, bbox[1] - 5), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255,255,255), 1)

        return frame

# Global instance
face_engine = FaceEngine()
