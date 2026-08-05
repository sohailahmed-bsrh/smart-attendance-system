import os
import shutil
import cv2
import threading
import time
from datetime import datetime
import pandas as pd
import customtkinter as ctk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.utils.config import config
from src.utils.helpers import BASE_DIR
from src.core.voice_engine import voice
from src.core.face_engine import face_engine
from src.core.database import get_attendance_data, export_to_excel, delete_attendance

def setup_treeview_style():
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview", background="#1F2937", foreground="white", rowheight=30,
                    fieldbackground="#1F2937", bordercolor="#374151", borderwidth=0, font=("Segoe UI", 11))
    style.map('Treeview', background=[('selected', '#3B82F6')])
    style.configure("Treeview.Heading", background="#111827", foreground="white", relief="flat", font=("Segoe UI", 12, "bold"))
    style.map("Treeview.Heading", background=[('active', '#374151')])

class CameraTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.camera_running = False
        self.capture = None
        
        # Split into left (Camera) and right (Stats/Attendance)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Camera)
        self.left_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        header_cam = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_cam.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header_cam, text="Live Camera Feed", font=("Segoe UI", 20, "bold"), text_color="white").pack(side="left")
        
        self.cam_label = ctk.CTkLabel(self.left_panel, text="Camera Offline", font=("Segoe UI", 16), width=640, height=480, fg_color="black", corner_radius=10)
        self.cam_label.pack(pady=10, padx=20, expand=True)
        
        controls = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        controls.pack(fill="x", pady=20, padx=20)
        
        self.btn_start = ctk.CTkButton(controls, text="▶ Start Camera", fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 14, "bold"), command=self.start_camera)
        self.btn_start.pack(side="left", padx=10)
        self.btn_stop = ctk.CTkButton(controls, text="⏹ Stop Camera", fg_color="#DC2626", hover_color="#991B1B", font=("Segoe UI", 14, "bold"), command=self.stop_camera, state="disabled")
        self.btn_stop.pack(side="left", padx=10)

        # Right Panel (Dashboard Stats)
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.lbl_clock = ctk.CTkLabel(self.right_panel, text="", font=("Segoe UI", 24, "bold"), text_color="#3B82F6")
        self.lbl_clock.pack(pady=(10, 20))
        
        # Stats Cards
        self.card_students = self._create_stat_card(self.right_panel, "Total Students", "0", "👨‍🎓")
        self.card_today = self._create_stat_card(self.right_panel, "Present Today", "0", "✅")
        
        # Recent Attendance List
        recent_frame = ctk.CTkFrame(self.right_panel, fg_color="#111827", corner_radius=15)
        recent_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(recent_frame, text="Recent Attendance", font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=10)
        
        self.recent_list = ctk.CTkTextbox(recent_frame, font=("Consolas", 12), fg_color="#1F2937", text_color="white")
        self.recent_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._update_clock()

    def _create_stat_card(self, parent, title, value, icon):
        card = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=10)
        card.pack(fill="x", pady=5)
        ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 30)).pack(side="left", padx=15, pady=15)
        v_box = ctk.CTkFrame(card, fg_color="transparent")
        v_box.pack(side="left", padx=10, pady=10, fill="y")
        ctk.CTkLabel(v_box, text=title, font=("Segoe UI", 12), text_color="#9CA3AF").pack(anchor="w")
        lbl_val = ctk.CTkLabel(v_box, text=value, font=("Segoe UI", 20, "bold"), text_color="white")
        lbl_val.pack(anchor="w")
        return lbl_val

    def _update_clock(self):
        self.lbl_clock.configure(text=datetime.now().strftime("%I:%M:%S %p\n%A, %d %b %Y"))
        self.after(1000, self._update_clock)
        
    def load_data(self):
        # Update Stats
        d = os.path.join(BASE_DIR, "datasets", "students")
        total = len([name for name in os.listdir(d) if os.path.isdir(os.path.join(d, name))]) if os.path.exists(d) else 0
        self.card_students.configure(text=str(total))
        
        df = get_attendance_data()
        today = datetime.now().strftime("%Y-%m-%d")
        present = len(df[df['Date'] == today]) if not df.empty else 0
        self.card_today.configure(text=str(present))
        
        # Update Recent List
        self.recent_list.configure(state="normal")
        self.recent_list.delete("1.0", "end")
        if not df.empty:
            recent = df.tail(10).iloc[::-1]
            for _, row in recent.iterrows():
                self.recent_list.insert("end", f"{row['Time']} - {row['Name']}\n")
        else:
            self.recent_list.insert("end", "No attendance records yet.")
        self.recent_list.configure(state="disabled")

    def start_camera(self):
        if self.camera_running: return
        self.capture = cv2.VideoCapture(config.get("camera_index", 0))
        if not self.capture.isOpened():
            messagebox.showerror("Error", "Camera Unavailable.")
            return
            
        self.camera_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        voice.speak("Camera started.")
        threading.Thread(target=self._loop, daemon=True).start()
        
    def stop_camera(self):
        if not self.camera_running: return
        self.camera_running = False
        if self.capture:
            self.capture.release()
        self.cam_label.configure(image="", text="Camera Stopped")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        voice.speak("Camera stopped.")
        
    def _loop(self):
        last_load = time.time()
        while self.camera_running and self.capture.isOpened():
            ret, frame = self.capture.read()
            if not ret: continue
            
            try:
                frame = face_engine.process_frame(frame)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb = cv2.resize(rgb, (640, 480))
                img = ImageTk.PhotoImage(Image.fromarray(rgb))
                self.cam_label.configure(image=img, text="")
                self.cam_label.image = img
                
                # Periodically update dashboard stats
                if time.time() - last_load > 2.0:
                    self.master.after(0, self.load_data)
                    last_load = time.time()
            except Exception as e:
                pass


class StudentsTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        setup_treeview_style()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header, text="Student Manager", font=("Segoe UI", 24, "bold")).pack(side="left")
        
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20)
        
        ctk.CTkButton(controls, text="🔄 Refresh", command=self.load_data, fg_color="#3B82F6").pack(side="left", padx=5)
        ctk.CTkButton(controls, text="🗑 Delete Selected", fg_color="#DC2626", hover_color="#991B1B", command=self.delete_student).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="⚙ Auto Re-Encode", fg_color="#F59E0B", hover_color="#D97706", command=self.encode).pack(side="right", padx=5)
        
        self.tree = ttk.Treeview(self, columns=("Name", "Images", "Path"), show="headings")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Images", text="Total Images")
        self.tree.heading("Path", text="Folder Path")
        self.tree.column("Name", width=200)
        self.tree.column("Images", width=100)
        self.tree.column("Path", width=400)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        
    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        d = os.path.join(BASE_DIR, "datasets", "students")
        if not os.path.exists(d): return
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.isdir(p):
                cnt = len([f for f in os.listdir(p) if f.endswith(('.jpg', '.png'))])
                self.tree.insert("", "end", values=(name, cnt, p))
                
    def delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student to delete.")
            return
        name = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete {name}?"):
            shutil.rmtree(os.path.join(BASE_DIR, "datasets", "students", name))
            self.load_data()
            face_engine.reload_embeddings()
            
    def encode(self):
        voice.speak("Encoding started.")
        face_engine.reload_embeddings()
        voice.speak("Encoding completed successfully.")
        messagebox.showinfo("Success", "Embeddings updated successfully.")


class RegisterTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.camera_running = False
        self.capture = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left - Preview
        self.left_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.left_panel, text="Live Preview", font=("Segoe UI", 20, "bold"), text_color="white").pack(pady=15)
        self.cam_label = ctk.CTkLabel(self.left_panel, text="Camera Offline", font=("Segoe UI", 16), width=480, height=360, fg_color="black", corner_radius=10)
        self.cam_label.pack(pady=10, padx=20, expand=True)
        
        # Right - Form
        self.right_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.right_panel, text="Register New Student", font=("Segoe UI", 24, "bold"), text_color="white").pack(pady=30)
        
        ctk.CTkLabel(self.right_panel, text="Full Name", font=("Segoe UI", 14), text_color="#9CA3AF").pack(anchor="w", padx=50)
        self.entry = ctk.CTkEntry(self.right_panel, width=300, height=40, font=("Segoe UI", 14))
        self.entry.pack(pady=10)
        
        self.btn_cam = ctk.CTkButton(self.right_panel, text="▶ Start Camera", command=self.start_camera, fg_color="#10B981", hover_color="#059669")
        self.btn_cam.pack(pady=10)
        
        self.btn_cap = ctk.CTkButton(self.right_panel, text="📸 Capture 5 Images", command=self.capture_images, state="disabled", fg_color="#3B82F6")
        self.btn_cap.pack(pady=20)
        
        self.status = ctk.CTkLabel(self.right_panel, text="", font=("Segoe UI", 14), text_color="#10B981")
        self.status.pack(pady=10)

    def start_camera(self):
        if self.camera_running: return
        self.capture = cv2.VideoCapture(config.get("camera_index", 0))
        if not self.capture.isOpened():
            messagebox.showerror("Error", "Camera Unavailable.")
            return
            
        self.camera_running = True
        self.btn_cam.configure(text="⏹ Stop Camera", command=self.stop_camera, fg_color="#DC2626", hover_color="#991B1B")
        self.btn_cap.configure(state="normal")
        threading.Thread(target=self._loop, daemon=True).start()
        
    def stop_camera(self):
        if not self.camera_running: return
        self.camera_running = False
        if self.capture:
            self.capture.release()
        self.cam_label.configure(image="", text="Camera Stopped")
        self.btn_cam.configure(text="▶ Start Camera", command=self.start_camera, fg_color="#10B981", hover_color="#059669")
        self.btn_cap.configure(state="disabled")
        
    def _loop(self):
        while self.camera_running and self.capture.isOpened():
            ret, frame = self.capture.read()
            if not ret: continue
            
            # Simple preview without recognition boxes during registration
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb = cv2.resize(rgb, (480, 360))
            img = ImageTk.PhotoImage(Image.fromarray(rgb))
            self.cam_label.configure(image=img, text="")
            self.cam_label.image = img
            
    def capture_images(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a student name.")
            return
            
        self.btn_cap.configure(state="disabled", text="Capturing...")
        
        def task():
            try:
                folder = os.path.join(BASE_DIR, "datasets", "students", name)
                os.makedirs(folder, exist_ok=True)
                
                count = 0
                while count < 5 and self.camera_running:
                    ret, frame = self.capture.read()
                    if ret:
                        cv2.imwrite(os.path.join(folder, f"{datetime.now().strftime('%H%M%S%f')}.jpg"), frame)
                        count += 1
                        self.master.after(0, lambda c=count: self.status.configure(text=f"Captured {c}/5"))
                    time.sleep(0.5)
                    
                self.stop_camera()
                face_engine.reload_embeddings()
                voice.speak("Registration completed successfully.")
                self.master.after(0, lambda: self.status.configure(text="Registration Complete! Models Updated."))
                self.master.after(0, lambda: self.entry.delete(0, 'end'))
            except Exception as e:
                self.master.after(0, lambda: self.status.configure(text=f"Error: {e}", text_color="red"))
            finally:
                self.master.after(0, lambda: self.btn_cap.configure(state="normal", text="📸 Capture 5 Images"))
                
        threading.Thread(target=task, daemon=True).start()


class AttendanceTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        setup_treeview_style()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header, text="Attendance Records", font=("Segoe UI", 24, "bold")).pack(side="left")
        
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20)
        
        # Search & Filter
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.load_data())
        ctk.CTkEntry(controls, textvariable=self.search_var, placeholder_text="🔍 Search Name...", width=200).pack(side="left", padx=5)
        
        self.date_var = ctk.StringVar()
        self.date_var.trace("w", lambda name, index, mode: self.load_data())
        ctk.CTkEntry(controls, textvariable=self.date_var, placeholder_text="📅 Filter Date (YYYY-MM-DD)...", width=200).pack(side="left", padx=5)
        
        ctk.CTkButton(controls, text="🔄 Clear Filters", command=self.clear_filters, fg_color="#6B7280").pack(side="left", padx=5)
        
        # Actions
        ctk.CTkButton(controls, text="🗑 Delete Selected", fg_color="#DC2626", hover_color="#991B1B", command=self.delete_records).pack(side="right", padx=5)
        
        self.tree = ttk.Treeview(self, columns=("Name", "Date", "Time"), show="headings")
        for col in ("Name", "Date", "Time"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        
    def clear_filters(self):
        self.search_var.set("")
        self.date_var.set("")
        self.load_data()
        
    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        df = get_attendance_data()
        if df.empty: return
        
        s = self.search_var.get().lower()
        d = self.date_var.get()
        
        for _, row in df.iterrows():
            if s and s not in str(row["Name"]).lower(): continue
            if d and d not in str(row["Date"]): continue
            self.tree.insert("", "end", values=(row["Name"], row["Date"], row["Time"]))
            
    def delete_records(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select records to delete.")
            return
            
        names = []
        dates = []
        for item in sel:
            vals = self.tree.item(item)['values']
            names.append(vals[0])
            dates.append(vals[1])
            
        if messagebox.askyesno("Confirm", f"Delete {len(sel)} records?"):
            success, msg = delete_attendance(names, dates)
            if success:
                messagebox.showinfo("Success", msg)
                self.load_data()
            else:
                messagebox.showerror("Error", msg)


class UnknownFacesTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header, text="Unknown Faces Viewer", font=("Segoe UI", 24, "bold")).pack(side="left")
        
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20)
        ctk.CTkButton(controls, text="🔄 Refresh", command=self.load_data).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="🗑 Clear All", fg_color="#DC2626", hover_color="#991B1B", command=self.clear_all).pack(side="left", padx=5)
        
        # Image grid (scrollable)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#111827", corner_radius=15)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
    def load_data(self):
        for w in self.scroll.winfo_children():
            w.destroy()
            
        d = os.path.join(BASE_DIR, "outputs", "unknown_faces")
        if not os.path.exists(d): return
        
        files = [f for f in os.listdir(d) if f.endswith(('.jpg', '.png'))]
        if not files:
            ctk.CTkLabel(self.scroll, text="No unknown faces saved.", font=("Segoe UI", 16)).pack(pady=50)
            return
            
        # Create a simple grid
        col = 0
        row = 0
        for f in files:
            path = os.path.join(d, f)
            img = Image.open(path)
            img.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(img)
            
            card = ctk.CTkFrame(self.scroll, fg_color="#1F2937")
            card.grid(row=row, column=col, padx=10, pady=10)
            
            lbl = ctk.CTkLabel(card, image=photo, text="")
            lbl.image = photo
            lbl.pack(padx=10, pady=10)
            
            ctk.CTkLabel(card, text=f, font=("Segoe UI", 10)).pack(pady=(0, 5))
            
            ctk.CTkButton(card, text="Delete", fg_color="#DC2626", width=100, command=lambda p=path: self.delete_file(p)).pack(pady=(0,10))
            
            col += 1
            if col > 4:
                col = 0
                row += 1
                
    def delete_file(self, path):
        try:
            os.remove(path)
            self.load_data()
        except:
            pass
            
    def clear_all(self):
        if messagebox.askyesno("Confirm", "Delete ALL unknown faces?"):
            d = os.path.join(BASE_DIR, "outputs", "unknown_faces")
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d, exist_ok=True)
            self.load_data()


class AnalyticsTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Analytics Dashboard", font=("Segoe UI", 24, "bold")).pack(pady=20)
        
        self.chart_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
    def load_data(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()
            
        df = get_attendance_data()
        if df.empty:
            ctk.CTkLabel(self.chart_frame, text="No attendance data to analyze.", font=("Segoe UI", 16)).pack(pady=50)
            return
            
        # Use dark background for plots
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), dpi=100)
        fig.patch.set_facecolor('#111827')
        ax1.set_facecolor('#111827')
        ax2.set_facecolor('#111827')
        
        # Bar chart
        counts = df['Date'].value_counts().sort_index()
        counts.plot(kind='bar', ax=ax1, color='#3B82F6')
        ax1.set_title("Daily Attendance Volume", color="white")
        ax1.tick_params(colors="white")
        
        # Pie chart
        top_students = df['Name'].value_counts().head(5)
        top_students.plot(kind='pie', ax=ax2, autopct='%1.1f%%', textprops={'color':"white"})
        ax2.set_title("Top 5 Attendees", color="white")
        ax2.set_ylabel('')
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="System Settings", font=("Segoe UI", 24, "bold")).pack(pady=30)
        
        panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15, width=600)
        panel.pack(pady=20, expand=True)
        panel.grid_propagate(False)
        
        # Using grid for alignment
        ctk.CTkLabel(panel, text="UI Theme:", font=("Segoe UI", 14)).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.opt_theme = ctk.CTkOptionMenu(panel, values=["Dark", "Light", "System"])
        self.opt_theme.set(config.get("theme", "Dark"))
        self.opt_theme.grid(row=0, column=1, padx=20, pady=15, sticky="w")
        
        ctk.CTkLabel(panel, text="Camera Index:", font=("Segoe UI", 14)).grid(row=1, column=0, padx=20, pady=15, sticky="w")
        self.entry_cam = ctk.CTkEntry(panel, width=140)
        self.entry_cam.insert(0, str(config.get("camera_index", 0)))
        self.entry_cam.grid(row=1, column=1, padx=20, pady=15, sticky="w")
        
        ctk.CTkLabel(panel, text="Recognition Threshold:", font=("Segoe UI", 14)).grid(row=2, column=0, padx=20, pady=15, sticky="w")
        self.sli_thresh = ctk.CTkSlider(panel, from_=10.0, to=80.0)
        self.sli_thresh.set(config.get("recognition_threshold", 25.0))
        self.sli_thresh.grid(row=2, column=1, padx=20, pady=15, sticky="w")
        
        ctk.CTkLabel(panel, text="Voice Volume:", font=("Segoe UI", 14)).grid(row=3, column=0, padx=20, pady=15, sticky="w")
        self.sli_vol = ctk.CTkSlider(panel, from_=0.0, to=1.0)
        self.sli_vol.set(config.get("voice_volume", 1.0))
        self.sli_vol.grid(row=3, column=1, padx=20, pady=15, sticky="w")
        
        self.chk_voice = ctk.CTkCheckBox(panel, text="Enable Voice Assistant")
        if config.get("voice_enabled", True): self.chk_voice.select()
        self.chk_voice.grid(row=4, column=0, columnspan=2, padx=20, pady=15, sticky="w")
        
        self.chk_unknown = ctk.CTkCheckBox(panel, text="Save Unknown Faces")
        if config.get("save_unknown_faces", True): self.chk_unknown.select()
        self.chk_unknown.grid(row=5, column=0, columnspan=2, padx=20, pady=15, sticky="w")
        
        ctk.CTkButton(panel, text="Save Settings", font=("Segoe UI", 14, "bold"), command=self.save, fg_color="#10B981").grid(row=6, column=0, columnspan=2, pady=20)
        
    def save(self):
        theme = self.opt_theme.get()
        config.set("theme", theme)
        ctk.set_appearance_mode(theme)
        
        try:
            cam_idx = int(self.entry_cam.get())
            config.set("camera_index", cam_idx)
        except:
            pass
            
        config.set("voice_enabled", bool(self.chk_voice.get()))
        config.set("voice_volume", self.sli_vol.get())
        config.set("recognition_threshold", self.sli_thresh.get())
        config.set("save_unknown_faces", bool(self.chk_unknown.get()))
        
        messagebox.showinfo("Success", "Settings Applied Successfully.")


class AboutTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(panel, text="🎯", font=("Segoe UI Emoji", 80)).pack(pady=(40, 10))
        ctk.CTkLabel(panel, text="SMART ATTENDANCE PRO", font=("Segoe UI", 28, "bold"), text_color="#3B82F6").pack(pady=5)
        ctk.CTkLabel(panel, text="Version 2.0 (Professional Edition)", font=("Segoe UI", 14), text_color="#9CA3AF").pack()
        
        ctk.CTkLabel(panel, text="Developed by Sohail Ahmed", font=("Segoe UI", 18, "bold")).pack(pady=(30, 5))
        ctk.CTkLabel(panel, text="Final Year Project", font=("Segoe UI", 14)).pack()
        
        ctk.CTkLabel(panel, text="Technologies Used: Python, CustomTkinter, OpenCV, InsightFace, Pyttsx3", font=("Segoe UI", 12), text_color="#6B7280").pack(pady=(40, 20), padx=40)


class HelpTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="User Guide", font=("Segoe UI", 24, "bold")).pack(pady=30)
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="#111827", corner_radius=15)
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        guide = """
# Quick Start Guide

1. Registration
   - Go to 'Register Student'
   - Enter full name and Start Camera
   - Ensure face is clearly visible, then 'Capture 5 Images'
   - The AI model will automatically encode the new face

2. Taking Attendance
   - Go to 'Start Attendance' (Camera Tab)
   - Click 'Start Camera'
   - The system will detect faces, show confidence levels, and mark attendance
   - Voice assistant will confirm successful attendance

3. Viewing Records
   - Go to 'View Attendance'
   - You can search by name or filter by date
   - Export reports directly to Excel from the Tools menu

4. Managing Students
   - Go to 'Student Manager'
   - View registered students, their image counts, and file paths
   - Delete students or manually re-encode the AI model

5. Settings
   - Adjust Camera Index if using an external webcam (e.g. 1 instead of 0)
   - Adjust recognition threshold (lower = stricter)
   - Toggle voice assistant and unknown face saving
"""
        textbox = ctk.CTkTextbox(scroll, font=("Segoe UI", 14), fg_color="transparent", text_color="white", wrap="word")
        textbox.pack(fill="both", expand=True, padx=20, pady=20)
        textbox.insert("1.0", guide)
        textbox.configure(state="disabled")
