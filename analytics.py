import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime
from utils import center_window
from config import settings

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

app.title("Analytics Dashboard")
app.resizable(False, False)
center_window(app, 1000, 700)
# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "outputs",
    "attendance.csv"
)

STUDENT_FOLDER = os.path.join(
    BASE_DIR,
    "datasets",
    "students"
)

# =====================================================
# LOAD DATA
# =====================================================

if os.path.exists(ATTENDANCE_FILE):

    df = pd.read_csv(ATTENDANCE_FILE)

else:

    df = pd.DataFrame(
        columns=[
            "Name",
            "Date",
            "Time"
        ]
    )

# =====================================================
# SUMMARY
# =====================================================

today = datetime.now().strftime("%Y-%m-%d")

today_df = df[df["Date"] == today]

total_students = 0

if os.path.exists(STUDENT_FOLDER):

    total_students = len(

        [

            f

            for f in os.listdir(STUDENT_FOLDER)

            if os.path.isdir(

                os.path.join(

                    STUDENT_FOLDER,

                    f

                )

            )

        ]

    )

today_attendance = len(today_df)

total_records = len(df)

# =====================================================
# TITLE
# =====================================================

title = ctk.CTkLabel(

    app,

    text="📊 Smart Attendance Analytics",

    font=("Arial",30,"bold")

)

title.pack(
    pady=20
)

# =====================================================
# DASHBOARD CARDS
# =====================================================

cards = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

cards.pack(
    pady=15
)

card1 = ctk.CTkFrame(
    cards,
    width=220,
    height=120
)

card1.grid(
    row=0,
    column=0,
    padx=20
)

ctk.CTkLabel(
    card1,
    text="👨‍🎓 Total Students",
    font=("Arial",18,"bold")
).pack(pady=(15,5))

ctk.CTkLabel(
    card1,
    text=str(total_students),
    font=("Arial",30,"bold")
).pack()

card2 = ctk.CTkFrame(
    cards,
    width=220,
    height=120
)

card2.grid(
    row=0,
    column=1,
    padx=20
)

ctk.CTkLabel(
    card2,
    text="✅ Today",
    font=("Arial",18,"bold")
).pack(pady=(15,5))

ctk.CTkLabel(
    card2,
    text=str(today_attendance),
    font=("Arial",30,"bold")
).pack()

card3 = ctk.CTkFrame(
    cards,
    width=220,
    height=120
)

card3.grid(
    row=0,
    column=2,
    padx=20
)

ctk.CTkLabel(
    card3,
    text="📋 Total Records",
    font=("Arial",18,"bold")
).pack(pady=(15,5))

ctk.CTkLabel(
    card3,
    text=str(total_records),
    font=("Arial",30,"bold")
).pack()

# =====================================================
# GRAPH AREA
# =====================================================

graph_frame = ctk.CTkFrame(app)

graph_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

# =====================================================
# CREATE FIGURE
# =====================================================

fig = plt.Figure(
    figsize=(11,5),
    dpi=100
)

# -------------------------------
# BAR CHART
# -------------------------------

ax1 = fig.add_subplot(121)

if len(df) > 0:

    attendance = df["Name"].value_counts()

    attendance.plot(
        kind="bar",
        ax=ax1,
        color="steelblue"
    )

    ax1.set_title(
        "Student Attendance"
    )

    ax1.set_xlabel(
        "Students"
    )

    ax1.set_ylabel(
        "Records"
    )

else:

    ax1.text(
        0.5,
        0.5,
        "No Data",
        ha="center",
        va="center",
        fontsize=16
    )

# -------------------------------
# PIE CHART
# -------------------------------

ax2 = fig.add_subplot(122)

if len(df) > 0:

    attendance.plot(
        kind="pie",
        autopct="%1.1f%%",
        ax=ax2
    )

    ax2.set_ylabel("")

    ax2.set_title(
        "Attendance Distribution"
    )

else:

    ax2.text(
        0.5,
        0.5,
        "No Data",
        ha="center",
        va="center",
        fontsize=16
    )

# =====================================================
# SHOW GRAPH
# =====================================================

canvas = FigureCanvasTkAgg(
    fig,
    master=graph_frame
)

canvas.draw()

canvas.get_tk_widget().pack(
    fill="both",
    expand=True
)

# =====================================================
# STATISTICS
# =====================================================

stats_frame = ctk.CTkFrame(app)

stats_frame.pack(
    fill="x",
    padx=20,
    pady=10
)

if len(df) > 0:

    most_regular = attendance.idxmax()

    most_count = attendance.max()

    least_regular = attendance.idxmin()

    least_count = attendance.min()

else:

    most_regular = "-"

    most_count = 0

    least_regular = "-"

    least_count = 0

stats = ctk.CTkLabel(

    stats_frame,

    text=(
        f"🏆 Most Regular : {most_regular} ({most_count})        "
        f"📉 Least Regular : {least_regular} ({least_count})"
    ),

    font=("Arial",16,"bold")

)

stats.pack(
    pady=10
)

# =====================================================
# FUNCTIONS
# =====================================================

def refresh_analytics():

    app.destroy()

    import subprocess
    import sys

    subprocess.Popen(
        [
            sys.executable,
            os.path.abspath(__file__)
        ]
    )


def export_report():

    from tkinter import messagebox

    messagebox.showinfo(
        "Coming Soon",
        "PDF & Excel Export will be available in the next update."
    )


def close_window():

    plt.close("all")

    app.destroy()


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
    width=180,
    height=42,
    command=refresh_analytics
).grid(
    row=0,
    column=0,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="📤 Export Report",
    width=180,
    height=42,
    command=export_report
).grid(
    row=0,
    column=1,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="❌ Close",
    width=180,
    height=42,
    fg_color="red",
    hover_color="darkred",
    command=close_window
).grid(
    row=0,
    column=2,
    padx=10
)

# =====================================================
# WINDOW CLOSE
# =====================================================

app.protocol(
    "WM_DELETE_WINDOW",
    close_window
)

# =====================================================
# RUN
# =====================================================

app.mainloop()