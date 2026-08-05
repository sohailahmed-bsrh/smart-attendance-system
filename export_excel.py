import customtkinter as ctk
import pandas as pd
import os

from datetime import datetime
from tkinter import messagebox

from config import settings
from utils import center_window

# =====================================================
# THEME
# =====================================================

ctk.set_appearance_mode(
    settings.get("theme", "dark").lower()
)

ctk.set_default_color_theme("blue")

# =====================================================
# WINDOW
# =====================================================

app = ctk.CTk()

app.title("Export Attendance")

app.resizable(False, False)
center_window(app, 550, 320)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "outputs",
    "attendance.csv"
)

EXPORT_FOLDER = os.path.join(
    BASE_DIR,
    "exports"
)

os.makedirs(
    EXPORT_FOLDER,
    exist_ok=True
)

# =====================================================
# TITLE
# =====================================================

title = ctk.CTkLabel(
    app,
    text="📤 Export Attendance",
    font=("Arial",28,"bold")
)

title.pack(
    pady=25
)

status_label = ctk.CTkLabel(
    app,
    text="Ready to export attendance.",
    font=("Arial",16)
)

status_label.pack(
    pady=15
)
# =====================================================
# EXPORT FUNCTION
# =====================================================

def export_attendance():

    if not os.path.exists(ATTENDANCE_FILE):

        messagebox.showerror(
            "Error",
            "Attendance file not found."
        )

        return

    try:

        df = pd.read_csv(
            ATTENDANCE_FILE
        )

        if df.empty:

            messagebox.showwarning(
                "Warning",
                "No attendance records found."
            )

            return

        filename = datetime.now().strftime(
            "Attendance_%Y%m%d_%H%M%S.xlsx"
        )

        export_file = os.path.join(
            EXPORT_FOLDER,
            filename
        )

        df.to_excel(
            export_file,
            index=False
        )

        status_label.configure(
            text="✅ Export Completed Successfully"
        )

        messagebox.showinfo(
            "Success",
            f"Attendance exported successfully.\n\nSaved at:\n{export_file}"
        )

    except Exception as e:

        messagebox.showerror(
            "Export Error",
            str(e)
        )

# =====================================================
# BUTTONS
# =====================================================

button_frame = ctk.CTkFrame(app)

button_frame.pack(
    pady=30
)

ctk.CTkButton(
    button_frame,
    text="📤 Export Excel",
    width=180,
    height=45,
    command=export_attendance
).grid(
    row=0,
    column=0,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="❌ Close",
    width=180,
    height=45,
    fg_color="red",
    hover_color="darkred",
    command=app.destroy
).grid(
    row=0,
    column=1,
    padx=10
)

# =====================================================
# WINDOW CLOSE
# =====================================================

app.protocol(
    "WM_DELETE_WINDOW",
    app.destroy
)

# =====================================================
# RUN
# =====================================================

app.mainloop()