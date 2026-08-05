import os
import threading
import subprocess
import queue
import time
from config import settings

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# Initialize pygame mixer
pygame.mixer.init()

_voice_queue = queue.Queue()
_voice_thread = None
_voice_thread_lock = threading.Lock()

VOICE_MODEL = "en-US-ChristopherNeural" # Professional Male voice
# VOICE_MODEL = "en-US-AriaNeural" # Professional Female voice

def _voice_worker():
    while True:
        text = _voice_queue.get()
        if text is None:
            break
            
        if not settings.get("voice", True):
            _voice_queue.task_done()
            continue
            
        try:
            # Generate audio file
            output_file = "temp_voice.mp3"
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
                    
            # Use edge-tts CLI
            subprocess.run(["edge-tts", "--voice", VOICE_MODEL, "--text", text, "--write-media", output_file], 
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Play audio
            if os.path.exists(output_file):
                pygame.mixer.music.load(output_file)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
                pygame.mixer.music.unload()
        except Exception as e:
            print(f"[VOICE ERROR] {e}")
        finally:
            _voice_queue.task_done()

def _ensure_voice_thread_running():
    global _voice_thread
    with _voice_thread_lock:
        if _voice_thread is None or not _voice_thread.is_alive():
            _voice_thread = threading.Thread(target=_voice_worker, daemon=True)
            _voice_thread.start()

def speak(text):
    """Queue a message to be spoken. Non-blocking, highly realistic voice."""
    _ensure_voice_thread_running()
    _voice_queue.put(text)
