import os
import cv2
import pickle
import numpy as np
from insightface.app import FaceAnalysis

# Initialize InsightFace
app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=-1, det_size=(640, 640))

DATASET_PATH = "datasets/students"
MODEL_PATH = "models"

known_embeddings = []
known_names = []

print("Encoding student faces...\n")

for student_name in os.listdir(DATASET_PATH):
    student_folder = os.path.join(DATASET_PATH, student_name)

    if not os.path.isdir(student_folder):
        continue

    print(f"Processing: {student_name}")

    for image_name in os.listdir(student_folder):
        image_path = os.path.join(student_folder, image_name)

        image = cv2.imread(image_path)

        if image is None:
            continue

        faces = app.get(image)

        if len(faces) == 0:
            print(f"  Face not found -> {image_name}")
            continue

        embedding = faces[0].embedding

        known_embeddings.append(embedding)
        known_names.append(student_name)

        print(f"  Encoded -> {image_name}")

# Save embeddings
os.makedirs(MODEL_PATH, exist_ok=True)

with open(os.path.join(MODEL_PATH, "face_embeddings.pkl"), "wb") as f:
    pickle.dump(
        {
            "embeddings": np.array(known_embeddings),
            "names": known_names,
        },
        f,
    )

print("\n=================================")
print("Encoding Completed Successfully!")
print(f"Total Encodings: {len(known_names)}")
print("Saved to models/face_embeddings.pkl")
print("=================================")