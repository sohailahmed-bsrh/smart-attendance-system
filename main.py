import os
import sys

# Ensure src/ modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from src.utils.config import config
from src.gui.splash import SplashScreen
from src.gui.login import LoginScreen
from src.core.voice_engine import voice
from src.core.face_engine import face_engine

ctk.set_appearance_mode(config.get("theme", "Dark"))
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide main window initially
        
        self.title("Smart Attendance System PRO")
        self.geometry("1366x768")
        self.minsize(1200, 700)
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1366 // 2)
        y = (self.winfo_screenheight() // 2) - (768 // 2)
        self.geometry(f"1366x768+{x}+{y}")
        
        # Handle safe exit
        self.protocol("WM_DELETE_WINDOW", self.exit_application)
        
        # Start Splash Screen
        self.splash = SplashScreen(self, self.on_splash_complete)

    def on_splash_complete(self):
        self.deiconify() # Show main window
        # Show Login Screen First
        self.login = LoginScreen(self, self.on_login_success)
        
    def on_login_success(self):
        from src.gui.dashboard import Dashboard
        self.dashboard = Dashboard(self)
        
    def exit_application(self):
        voice.speak("System shutting down.")
        
        # Stop camera safely if running
        if hasattr(self, 'dashboard'):
            try:
                # If there's a camera tab running, we should stop it
                if hasattr(self.dashboard, 'tabs') and 'camera' in self.dashboard.tabs:
                    cam_tab = self.dashboard.tabs['camera']
                    if hasattr(cam_tab, 'stop_camera'):
                        cam_tab.stop_camera()
            except Exception:
                pass
                
        # Give voice engine a moment to speak
        self.after(1500, self._destroy_app)
        
    def _destroy_app(self):
        self.quit()
        self.destroy()
        os._exit(0) # Force exit to ensure daemon threads are killed

if __name__ == "__main__":
    app = App()
    app.mainloop()
