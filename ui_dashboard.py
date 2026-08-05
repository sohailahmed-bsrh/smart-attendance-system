import customtkinter as ctk
from tkinter import ttk, messagebox
import cv2
import threading
import queue
import os
import sys
import subprocess
import shutil
import pandas as pd
from datetime import datetime
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import settings
from attendance_system import recognize_frame, reload_embeddings, get_total_students

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_DIR = os.path.join(BASE_DIR, "datasets", "students")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "outputs", "attendance.csv")
ENCODE_SCRIPT = "encode_faces.py"

class MainDashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.master = master
        self.pack(fill="both", expand=True)

        self.camera_running = False
        self.capture = None
        self.camera_thread = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="🎓 SMART\nATTENDANCE", font=("Arial", 22, "bold"), justify="center").pack(pady=30)

        self.btn_dash = self._make_nav_btn("Dashboard", self._show_dashboard)
        self.btn_students = self._make_nav_btn("Manage Students", self._show_students)
        self.btn_register = self._make_nav_btn("Register New", self._show_register)
        self.btn_analytics = self._make_nav_btn("Analytics", self._show_analytics)
        self.btn_settings = self._make_nav_btn("Settings", self._show_settings)

        ctk.CTkButton(self.sidebar, text="Logout", fg_color="red", hover_color="darkred", command=self._logout).pack(side="bottom", pady=20, padx=20)

        # Main Content Area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # Initialize Tabs
        self.frames = {}
        self.frames['dashboard'] = self._create_dashboard_frame()
        self.frames['students'] = self._create_students_frame()
        self.frames['register'] = self._create_register_frame()
        self.frames['analytics'] = self._create_analytics_frame()
        self.frames['settings'] = self._create_settings_frame()

        self._show_dashboard()

    def _make_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30"), anchor="w", font=("Arial", 16), command=command)
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def _hide_all_frames(self):
        for frame in self.frames.values():
            frame.pack_forget()
        for btn in [self.btn_dash, self.btn_students, self.btn_register, self.btn_analytics, self.btn_settings]:
            btn.configure(fg_color="transparent")

    # ==========================
    # Dashboard Tab
    # ==========================
    def _create_dashboard_frame(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        # Header Stats
        stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        self.lbl_tot_students = ctk.CTkLabel(stats_frame, text="Total Students: 0", font=("Arial", 18, "bold"))
        self.lbl_tot_students.pack(side="left", padx=20)
        
        self.lbl_tot_today = ctk.CTkLabel(stats_frame, text="Present Today: 0", font=("Arial", 18, "bold"))
        self.lbl_tot_today.pack(side="left", padx=20)
        
        # Camera Area
        cam_panel = ctk.CTkFrame(frame)
        cam_panel.pack(fill="both", expand=True, padx=20, pady=10)
        
        controls = ctk.CTkFrame(cam_panel, fg_color="transparent")
        controls.pack(fill="x", pady=10)
        
        ctk.CTkButton(controls, text="▶ Start Camera", fg_color="green", hover_color="darkgreen", command=self.start_camera).pack(side="left", padx=20)
        ctk.CTkButton(controls, text="⏹ Stop Camera", fg_color="red", hover_color="darkred", command=self.stop_camera).pack(side="left")
        
        self.cam_label = ctk.CTkLabel(cam_panel, text="Camera is Stopped", width=640, height=480, bg_color="black")
        self.cam_label.pack(pady=10)
        
        self.last_recognized_lbl = ctk.CTkLabel(cam_panel, text="Waiting for recognition...", font=("Arial", 16))
        self.last_recognized_lbl.pack(pady=10)

        return frame

    def _show_dashboard(self):
        self._hide_all_frames()
        self.frames['dashboard'].pack(fill="both", expand=True)
        self.btn_dash.configure(fg_color=("gray75", "gray25"))
        self._load_data()

    # ==========================
    # Camera Logic
    # ==========================
    def start_camera(self):
        if self.camera_running: return
        self.capture = cv2.VideoCapture(settings.get("camera", 0))
        if not self.capture.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            return
        self.camera_running = True
        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()

    def stop_camera(self):
        self.camera_running = False
        if self.capture:
            self.capture.release()
        self.cam_label.configure(image=None, text="Camera is Stopped")

    def _camera_loop(self):
        while self.camera_running and self.capture.isOpened():
            ret, frame = self.capture.read()
            if not ret: continue
            
            try:
                annotated_frame, person = recognize_frame(frame)
                if person:
                    self.last_recognized_lbl.configure(text=f"Last Recognized: {person}")
                    
                # Convert for Tkinter
                rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                rgb = cv2.resize(rgb, (640, 480))
                img = ImageTk.PhotoImage(Image.fromarray(rgb))
                
                self.cam_label.configure(image=img, text="")
                self.cam_label.image = img
            except Exception as e:
                pass

    # ==========================
    # Students Tab
    # ==========================
    def _create_students_frame(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        ctk.CTkLabel(frame, text="Manage Students", font=("Arial", 24, "bold")).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        ctk.CTkButton(btn_frame, text="Refresh", command=self._load_students_list).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Delete Selected", fg_color="red", command=self._delete_student).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Train Model", fg_color="orange", text_color="black", command=self._train_model).pack(side="left", padx=10)

        self.tree = ttk.Treeview(frame, columns=("Name", "Images"), show="headings", height=20)
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Images", text="Image Count")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        
        return frame

    def _show_students(self):
        self.stop_camera()
        self._hide_all_frames()
        self.frames['students'].pack(fill="both", expand=True)
        self.btn_students.configure(fg_color=("gray75", "gray25"))
        self._load_students_list()

    def _load_students_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not os.path.exists(STUDENTS_DIR): return
        for name in sorted(os.listdir(STUDENTS_DIR)):
            folder = os.path.join(STUDENTS_DIR, name)
            if os.path.isdir(folder):
                images = len([f for f in os.listdir(folder) if f.endswith('.jpg')])
                self.tree.insert("", "end", values=(name, images))

    def _delete_student(self):
        selected = self.tree.selection()
        if not selected: return
        name = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            shutil.rmtree(os.path.join(STUDENTS_DIR, name))
            self._load_students_list()

    def _train_model(self):
        try:
            subprocess.run([sys.executable, ENCODE_SCRIPT], check=True)
            reload_embeddings()
            messagebox.showinfo("Success", "Model trained successfully!")
            self._load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Training failed: {e}")

    # ==========================
    # Register Tab
    # ==========================
    def _create_register_frame(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        ctk.CTkLabel(frame, text="Register New Student", font=("Arial", 24, "bold")).pack(pady=30)
        
        panel = ctk.CTkFrame(frame)
        panel.pack(pady=20, padx=50, fill="x")
        
        ctk.CTkLabel(panel, text="Student Name:", font=("Arial", 16)).pack(pady=10)
        self.reg_name = ctk.CTkEntry(panel, width=300, font=("Arial", 16))
        self.reg_name.pack(pady=10)
        
        self.reg_btn = ctk.CTkButton(panel, text="Capture 5 Images", font=("Arial", 16), command=self._capture_registration)
        self.reg_btn.pack(pady=20)
        
        self.reg_status = ctk.CTkLabel(panel, text="", font=("Arial", 14), text_color="green")
        self.reg_status.pack(pady=10)
        
        return frame

    def _show_register(self):
        self.stop_camera()
        self._hide_all_frames()
        self.frames['register'].pack(fill="both", expand=True)
        self.btn_register.configure(fg_color=("gray75", "gray25"))

    def _capture_registration(self):
        name = self.reg_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Enter a name")
            return
            
        self.reg_btn.configure(state="disabled", text="Capturing...")
        
        def task():
            try:
                folder = os.path.join(STUDENTS_DIR, name)
                os.makedirs(folder, exist_ok=True)
                cap = cv2.VideoCapture(settings.get("camera", 0))
                
                count = 0
                while count < 5:
                    ret, frame = cap.read()
                    if ret:
                        cv2.imwrite(os.path.join(folder, f"{datetime.now().strftime('%H%M%S%f')}.jpg"), frame)
                        count += 1
                        self.reg_status.configure(text=f"Captured {count}/5")
                    import time; time.sleep(0.5)
                cap.release()
                self.reg_status.configure(text="Capture complete! Please Train Model in Students Tab.")
                self.reg_name.delete(0, 'end')
            except Exception as e:
                self.reg_status.configure(text=f"Error: {e}", text_color="red")
            finally:
                self.reg_btn.configure(state="normal", text="Capture 5 Images")
                
        threading.Thread(target=task, daemon=True).start()

    # ==========================
    # Analytics Tab
    # ==========================
    def _create_analytics_frame(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        ctk.CTkLabel(frame, text="Attendance Analytics", font=("Arial", 24, "bold")).pack(pady=20)
        self.chart_frame = ctk.CTkFrame(frame)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=20)
        return frame

    def _show_analytics(self):
        self.stop_camera()
        self._hide_all_frames()
        self.frames['analytics'].pack(fill="both", expand=True)
        self.btn_analytics.configure(fg_color=("gray75", "gray25"))
        self._render_charts()

    def _render_charts(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        if not os.path.exists(ATTENDANCE_FILE):
            ctk.CTkLabel(self.chart_frame, text="No Data Available").pack(pady=50)
            return
            
        try:
            df = pd.read_csv(ATTENDANCE_FILE)
            if df.empty: return
            
            fig = plt.Figure(figsize=(8, 5), dpi=100)
            ax = fig.add_subplot(111)
            
            counts = df['Name'].value_counts().head(10)
            counts.plot(kind="bar", ax=ax, color="steelblue")
            ax.set_title("Top 10 Attendance")
            ax.set_xlabel("Student Name")
            ax.set_ylabel("Records")
            
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            ctk.CTkLabel(self.chart_frame, text=f"Error generating chart: {e}").pack(pady=50)

    # ==========================
    # Settings Tab
    # ==========================
    def _create_settings_frame(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        ctk.CTkLabel(frame, text="System Settings", font=("Arial", 24, "bold")).pack(pady=30)
        
        panel = ctk.CTkFrame(frame)
        panel.pack(pady=20, padx=50, fill="x")
        
        ctk.CTkLabel(panel, text="Camera Index:").pack(pady=5)
        self.set_cam = ctk.CTkEntry(panel)
        self.set_cam.insert(0, str(settings.get("camera", 0)))
        self.set_cam.pack(pady=5)
        
        self.set_voice = ctk.CTkCheckBox(panel, text="Enable Voice Announcements")
        if settings.get("voice", True): self.set_voice.select()
        self.set_voice.pack(pady=20)
        
        ctk.CTkButton(panel, text="Save Settings", command=self._save_settings).pack(pady=20)
        return frame

    def _show_settings(self):
        self.stop_camera()
        self._hide_all_frames()
        self.frames['settings'].pack(fill="both", expand=True)
        self.btn_settings.configure(fg_color=("gray75", "gray25"))

    def _save_settings(self):
        import json
        settings["camera"] = int(self.set_cam.get())
        settings["voice"] = bool(self.set_voice.get())
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        messagebox.showinfo("Success", "Settings saved.")

    # ==========================
    # Misc
    # ==========================
    def _load_data(self):
        self.lbl_tot_students.configure(text=f"Total Students: {get_total_students()}")
        
        today_count = 0
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE)
            today = datetime.now().strftime("%Y-%m-%d")
            today_count = int((df["Date"] == today).sum())
        self.lbl_tot_today.configure(text=f"Present Today: {today_count}")

    def _logout(self):
        self.stop_camera()
        self.master.show_login()
