import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DIRECTORIES = [
    "datasets",
    "datasets/students",
    "outputs",
    "outputs/unknown_faces",
    "outputs/exports",
    "models"
]

def setup_directories():
    """Ensure all required directories exist."""
    for d in DIRECTORIES:
        path = os.path.join(BASE_DIR, d)
        os.makedirs(path, exist_ok=True)

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
