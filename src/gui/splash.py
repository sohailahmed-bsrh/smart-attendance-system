import customtkinter as ctk
from PIL import Image
import threading
import time

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.parent = parent
        self.on_complete = on_complete
        
        self.title("Loading...")
        self.geometry("640x420")
        self.overrideredirect(True) # Remove window borders
        self.attributes("-topmost", True)
        
        # Center screen
        self.update_idletasks()
        w = 640
        h = 420
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.configure(fg_color="#0B0F19") # Deep Professional Dark
        
        # Main Container to simulate a border
        self.container = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15, border_width=1, border_color="#1F2937")
        self.container.pack(fill="both", expand=True, padx=2, pady=2)
        
        # UI Elements
        ctk.CTkLabel(self.container, text="🎯", font=("Segoe UI Emoji", 70)).pack(pady=(50, 10))
        ctk.CTkLabel(self.container, text="SMART ATTENDANCE PRO", font=("Segoe UI", 26, "bold"), text_color="#3B82F6").pack(pady=(10, 5))
        ctk.CTkLabel(self.container, text="Intelligent Face Recognition System", font=("Segoe UI", 14), text_color="#9CA3AF").pack(pady=0)
        ctk.CTkLabel(self.container, text="Developed by Sohail Ahmed", font=("Segoe UI", 12), text_color="#4B5563").pack(pady=(5, 20))
        
        self.progress = ctk.CTkProgressBar(self.container, width=450, height=8, progress_color="#3B82F6", fg_color="#1F2937")
        self.progress.pack(pady=(40, 15))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.container, text="Initializing...", font=("Segoe UI", 12), text_color="#9CA3AF")
        self.lbl_status.pack()

        # Start loading thread
        threading.Thread(target=self.load_resources, daemon=True).start()

    def update_progress(self, val, text):
        self.progress.set(val)
        self.lbl_status.configure(text=text)

    def load_resources(self):
        try:
            self.update_progress(0.1, "Checking Directories...")
            from src.utils.helpers import setup_directories
            setup_directories()
            time.sleep(0.5)

            self.update_progress(0.3, "Loading Configuration...")
            from src.utils.config import config
            time.sleep(0.5)

            self.update_progress(0.5, "Initializing Voice Assistant...")
            from src.core.voice_engine import voice
            voice.speak("System Started.")
            time.sleep(0.5)

            self.update_progress(0.7, "Loading AI Models (InsightFace)...")
            from src.core.face_engine import face_engine
            # face_engine initializes on import via singleton
            
            self.update_progress(1.0, "Preparing Dashboard...")
            time.sleep(0.5)
            
            # Switch to main thread for GUI update
            self.after(100, self.finish)
        except Exception as e:
            print(f"[SPLASH ERROR] {e}")
            self.after(100, self.finish)

    def finish(self):
        self.destroy()
        self.on_complete()
