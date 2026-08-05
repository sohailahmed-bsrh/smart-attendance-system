import customtkinter as ctk
from tkinter import messagebox
from src.gui.tabs import CameraTab, StudentsTab, RegisterTab, AttendanceTab, AnalyticsTab, SettingsTab, UnknownFacesTab, AboutTab, HelpTab
from src.core.face_engine import face_engine
from src.core.database import export_to_excel
from src.core.voice_engine import voice

class Dashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.master = master
        self.pack(fill="both", expand=True)

        self._setup_ui()

    def _setup_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#111827")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Branding
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(25, 20))
        ctk.CTkLabel(brand_frame, text="🎯", font=("Segoe UI Emoji", 34)).pack(side="left", padx=5)
        ctk.CTkLabel(brand_frame, text="SMART\nATTENDANCE", font=("Segoe UI", 16, "bold"), text_color="#3B82F6", justify="left").pack(side="left")

        # Scrollable area for buttons if screen is small
        self.scroll_sidebar = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", bg_color="transparent")
        self.scroll_sidebar.pack(fill="both", expand=True, padx=5, pady=5)

        self.buttons = {}
        
        # Core Features
        self._add_nav_btn("camera", "▶ Start Attendance", lambda: self._show_tab('camera'))
        self._add_nav_btn("register", "👤 Register Student", lambda: self._show_tab('register'))
        self._add_nav_btn("attendance", "📋 View Attendance", lambda: self._show_tab('attendance'))
        self._add_nav_btn("analytics", "📊 Analytics", lambda: self._show_tab('analytics'))
        self._add_nav_btn("students", "👨‍🎓 Student Manager", lambda: self._show_tab('students'))
        self._add_nav_btn("unknown", "❓ Unknown Faces", lambda: self._show_tab('unknown'))
        
        # Tools
        ctk.CTkLabel(self.scroll_sidebar, text="TOOLS", font=("Segoe UI", 12, "bold"), text_color="#6B7280", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        self._add_nav_btn("encode", "🔄 Encode Faces", self._encode_faces_action)
        self._add_nav_btn("export", "📤 Export / Reports", self._export_action)
        self._add_nav_btn("stop_cam", "⏹ Stop Camera", self._stop_camera_action)
        
        # System
        ctk.CTkLabel(self.scroll_sidebar, text="SYSTEM", font=("Segoe UI", 12, "bold"), text_color="#6B7280", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        self._add_nav_btn("settings", "⚙ Settings", lambda: self._show_tab('settings'))
        self._add_nav_btn("help", "💡 Help", lambda: self._show_tab('help'))
        self._add_nav_btn("about", "ℹ About", lambda: self._show_tab('about'))

        # Exit
        btn_exit = ctk.CTkButton(
            self.sidebar, text="❌ Exit Application", fg_color="#DC2626", text_color="white",
            hover_color="#991B1B", anchor="center", font=("Segoe UI", 14, "bold"), 
            command=self.master.exit_application, height=40
        )
        btn_exit.pack(side="bottom", fill="x", pady=20, padx=15)

        # Main Content
        self.content_area = ctk.CTkFrame(self, fg_color="#0B0F19")
        self.content_area.pack(side="right", fill="both", expand=True)

        # Tabs initialization
        self.tabs = {
            'camera': CameraTab(self.content_area),
            'students': StudentsTab(self.content_area),
            'register': RegisterTab(self.content_area),
            'attendance': AttendanceTab(self.content_area),
            'analytics': AnalyticsTab(self.content_area),
            'settings': SettingsTab(self.content_area),
            'unknown': UnknownFacesTab(self.content_area),
            'about': AboutTab(self.content_area),
            'help': HelpTab(self.content_area)
        }
        
        self._show_tab('camera')

    def _add_nav_btn(self, name, text, command):
        btn = ctk.CTkButton(
            self.scroll_sidebar, text=text, fg_color="transparent", text_color="#D1D5DB",
            hover_color="#1F2937", anchor="w", font=("Segoe UI", 14), height=38, command=command
        )
        btn.pack(fill="x", padx=5, pady=2)
        self.buttons[name] = btn

    def _show_tab(self, name):
        # Always attempt to stop camera if navigating away from camera or register tab
        # We handle this gracefully inside the tabs or just allow the tab to keep running if we want background cam?
        # Standard behavior: only stop if explicitly requested, but to avoid multiple cams, let's stop it.
        if name not in ['camera', 'register']:
            self._stop_camera_action(silent=True)
            
        for k, tab in self.tabs.items():
            tab.pack_forget()
        
        # Reset button colors
        for k, btn in self.buttons.items():
            if k not in ['encode', 'export', 'stop_cam']:
                btn.configure(fg_color="transparent", text_color="#D1D5DB")
            
        self.tabs[name].pack(fill="both", expand=True)
        
        # Highlight active tab
        if name in self.buttons:
            self.buttons[name].configure(fg_color="#1F2937", text_color="#3B82F6")
        
        # Load data if supported
        if hasattr(self.tabs[name], 'load_data'):
            self.tabs[name].load_data()

    def _encode_faces_action(self):
        voice.speak("Encoding started.")
        face_engine.reload_embeddings()
        voice.speak("Encoding completed successfully.")
        messagebox.showinfo("Success", "Faces encoded and model updated successfully.")
        
    def _export_action(self):
        success, msg = export_to_excel()
        if success:
            messagebox.showinfo("Export Successful", f"Attendance report generated:\n{msg}")
        else:
            messagebox.showerror("Export Failed", msg)
            
    def _stop_camera_action(self, silent=False):
        stopped = False
        if 'camera' in self.tabs and hasattr(self.tabs['camera'], 'stop_camera'):
            if self.tabs['camera'].camera_running:
                self.tabs['camera'].stop_camera()
                stopped = True
        if 'register' in self.tabs and hasattr(self.tabs['register'], 'stop_camera'):
            if getattr(self.tabs['register'], 'camera_running', False):
                self.tabs['register'].stop_camera()
                stopped = True
                
        if not silent and stopped:
            messagebox.showinfo("Camera Stopped", "Camera feed has been safely stopped.")
