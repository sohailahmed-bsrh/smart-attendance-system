import pyttsx3
import queue
import threading
from src.utils.config import config

class VoiceEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance
        
    def _init_engine(self):
        self._queue = queue.Queue()
        self._thread = None
        self._lock = threading.Lock()
        
    def _worker(self):
        # Engine must be initialized in the thread that uses it
        try:
            engine = pyttsx3.init()
        except Exception as e:
            print(f"[VOICE] Could not initialize pyttsx3: {e}")
            return
            
        while True:
            text = self._queue.get()
            if text is None:
                break
                
            if not config.get("voice_enabled"):
                self._queue.task_done()
                continue
                
            try:
                # Apply current settings
                rate = config.get("voice_rate")
                volume = config.get("voice_volume")
                engine.setProperty('rate', rate)
                engine.setProperty('volume', volume)
                
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[VOICE ERROR] {e}")
            finally:
                self._queue.task_done()

    def _ensure_running(self):
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._worker, daemon=True)
                self._thread.start()

    def speak(self, text):
        """Queue a message to be spoken. Non-blocking."""
        self._ensure_running()
        self._queue.put(text)

# Global instance
voice = VoiceEngine()
