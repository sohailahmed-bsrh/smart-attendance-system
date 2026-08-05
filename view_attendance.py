import customtkinter as ctk
from tkinter import ttk
import pandas as pd
import os

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

app.title("Attendance Records")
app.resizable(False, False)
center_window(app, 1366, 768)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "outputs",
    "attendance.csv"
)

# =====================================================
# TITLE
# =====================================================

title = ctk.CTkLabel(
    app,
    text="📋 Attendance Records",
    font=("Arial",30,"bold")
)

title.pack(pady=20)

# =====================================================
# SEARCH
# =====================================================

search_frame = ctk.CTkFrame(app)

search_frame.pack(
    fill="x",
    padx=20
)

search_entry = ctk.CTkEntry(
    search_frame,
    width=320,
    placeholder_text="Search Student..."
)

search_entry.pack(
    side="left",
    padx=10,
    pady=10
)

# =====================================================
# TABLE
# =====================================================

tree = ttk.Treeview(
    app,
    columns=(
        "Name",
        "Date",
        "Time"
    ),
    show="headings",
    height=24
)

tree.heading("Name", text="Student")

tree.heading("Date", text="Date")

tree.heading("Time", text="Time")

tree.column(
    "Name",
    width=350,
    anchor="center"
)

tree.column(
    "Date",
    width=220,
    anchor="center"
)

tree.column(
    "Time",
    width=220,
    anchor="center"
)

tree.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)
# =====================================================
# LOAD ATTENDANCE
# =====================================================

def load_attendance(search=""):

    for item in tree.get_children():
        tree.delete(item)

    if not os.path.exists(ATTENDANCE_FILE):
        total_label.configure(text="Total Records : 0")
        return

    try:

        df = pd.read_csv(ATTENDANCE_FILE)

        if search != "":

            df = df[
                df["Name"].str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        for _, row in df.iterrows():

            tree.insert(
                "",
                "end",
                values=(
                    row["Name"],
                    row["Date"],
                    row["Time"]
                )
            )

        total_label.configure(
            text=f"Total Records : {len(df)}"
        )

    except Exception as e:

        print(e)

# =====================================================
# SEARCH
# =====================================================

def search_attendance(event=None):

    load_attendance(
        search_entry.get().strip()
    )

search_entry.bind(
    "<KeyRelease>",
    search_attendance
)

# =====================================================
# TOTAL RECORDS
# =====================================================

total_label = ctk.CTkLabel(
    app,
    text="Total Records : 0",
    font=("Arial",16,"bold")
)

total_label.pack(
    pady=10
)

# =====================================================
# REFRESH
# =====================================================

def refresh_attendance():

    search_entry.delete(0, "end")

    load_attendance()

load_attendance()

# =====================================================
# EXPORT TO EXCEL
# =====================================================

def export_excel():

    if not os.path.exists(ATTENDANCE_FILE):

        ctk.CTkMessagebox(
            title="No Data",
            message="Attendance file not found."
        )

        return

    try:

        export_folder = os.path.join(
            BASE_DIR,
            "exports"
        )

        os.makedirs(
            export_folder,
            exist_ok=True
        )

        export_file = os.path.join(
            export_folder,
            "Attendance_Report.xlsx"
        )

        df = pd.read_csv(
            ATTENDANCE_FILE
        )

        df.to_excel(
            export_file,
            index=False
        )

        from tkinter import messagebox

        messagebox.showinfo(
            "Success",
            f"Attendance exported successfully.\n\n{export_file}"
        )

    except Exception as e:

        from tkinter import messagebox

        messagebox.showerror(
            "Export Error",
            str(e)
        )

# =====================================================
# CLEAR ATTENDANCE
# =====================================================

def clear_attendance():

    from tkinter import messagebox

    if not os.path.exists(ATTENDANCE_FILE):
        return

    if not messagebox.askyesno(
        "Confirm",
        "Delete all attendance records?"
    ):
        return

    pd.DataFrame(
        columns=[
            "Name",
            "Date",
            "Time"
        ]
    ).to_csv(
        ATTENDANCE_FILE,
        index=False
    )

    load_attendance()

# =====================================================
# BUTTONS
# =====================================================

button_frame = ctk.CTkFrame(app)

button_frame.pack(
    pady=15
)

ctk.CTkButton(
    button_frame,
    text="🔄 Refresh",
    width=170,
    command=refresh_attendance
).grid(
    row=0,
    column=0,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="📤 Export Excel",
    width=170,
    command=export_excel
).grid(
    row=0,
    column=1,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="🗑 Clear Records",
    width=170,
    fg_color="orange",
    hover_color="#CC8400",
    command=clear_attendance
).grid(
    row=0,
    column=2,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="❌ Close",
    width=170,
    fg_color="red",
    hover_color="darkred",
    command=app.destroy
).grid(
    row=0,
    column=3,
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