import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import shutil
import subprocess
import sys
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

app.title("Student Manager")
app.resizable(False, False)
center_window(app, 1366, 768)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STUDENT_FOLDER = os.path.join(
    BASE_DIR,
    "datasets",
    "students"
)

# =====================================================
# TITLE
# =====================================================

title = ctk.CTkLabel(
    app,
    text="👨‍🎓 Student Manager",
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
    placeholder_text="Search Student...",
    width=300
)

search_entry.pack(
    side="left",
    padx=10,
    pady=10
)

# =====================================================
# STUDENT LIST
# =====================================================

tree = ttk.Treeview(
    app,
    columns=(
        "Name",
        "Images"
    ),
    show="headings",
    height=22
)

tree.heading(
    "Name",
    text="Student Name"
)

tree.heading(
    "Images",
    text="Images"
)

tree.column(
    "Name",
    width=500,
    anchor="center"
)

tree.column(
    "Images",
    width=120,
    anchor="center"
)

tree.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

# =====================================================
# LOAD STUDENTS
# =====================================================

def load_students(search_text=""):

    for item in tree.get_children():
        tree.delete(item)

    if not os.path.exists(STUDENT_FOLDER):
        return

    students = sorted(os.listdir(STUDENT_FOLDER))

    for student in students:

        folder = os.path.join(
            STUDENT_FOLDER,
            student
        )

        if not os.path.isdir(folder):
            continue

        if (
            search_text != ""
            and
            search_text.lower()
            not in student.lower()
        ):
            continue

        image_count = len(

            [

                f

                for f in os.listdir(folder)

                if f.lower().endswith(
                    (
                        ".jpg",
                        ".jpeg",
                        ".png"
                    )
                )

            ]

        )

        tree.insert(

            "",

            "end",

            values=(

                student,

                image_count

            )

        )


# =====================================================
# SEARCH
# =====================================================

def search_student(event=None):

    load_students(

        search_entry.get().strip()

    )


search_entry.bind(

    "<KeyRelease>",

    search_student

)

# =====================================================
# STUDENT INFO
# =====================================================

info_frame = ctk.CTkFrame(app)

info_frame.pack(

    fill="x",

    padx=20,

    pady=10

)

student_info = ctk.CTkLabel(

    info_frame,

    text="Select a student to view details.",

    font=("Arial",16)

)

student_info.pack(

    pady=10

)


def show_student(event):

    selected = tree.selection()

    if not selected:
        return

    values = tree.item(
        selected[0]
    )["values"]

    student = values[0]

    images = values[1]

    folder = os.path.join(
        STUDENT_FOLDER,
        student
    )

    student_info.configure(

        text=

        f"👤 Name : {student}\n\n"

        f"🖼 Images : {images}\n\n"

        f"📁 Folder : {folder}"

    )


tree.bind(

    "<<TreeviewSelect>>",

    show_student

)

# =====================================================
# REFRESH
# =====================================================

def refresh_students():

    load_students()

    student_info.configure(

        text="Student list refreshed."

    )

load_students()

# =====================================================
# RENAME STUDENT
# =====================================================

def rename_student():

    selected = tree.selection()

    if not selected:

        messagebox.showwarning(
            "Warning",
            "Select a student first."
        )

        return

    old_name = tree.item(
        selected[0]
    )["values"][0]

    dialog = ctk.CTkInputDialog(
        text="Enter New Student Name",
        title="Rename Student"
    )

    new_name = dialog.get_input()

    if not new_name:
        return

    old_folder = os.path.join(
        STUDENT_FOLDER,
        old_name
    )

    new_folder = os.path.join(
        STUDENT_FOLDER,
        new_name.strip()
    )

    if os.path.exists(new_folder):

        messagebox.showerror(
            "Error",
            "Student already exists."
        )

        return

    os.rename(
        old_folder,
        new_folder
    )

    subprocess.run(
        [
            sys.executable,
            os.path.join(
                BASE_DIR,
                "encode_faces.py"
            )
        ]
    )

    load_students()

    messagebox.showinfo(
        "Success",
        "Student renamed successfully."
    )

# =====================================================
# DELETE STUDENT
# =====================================================

def delete_student():

    selected = tree.selection()

    if not selected:

        messagebox.showwarning(
            "Warning",
            "Select a student first."
        )

        return

    student = tree.item(
        selected[0]
    )["values"][0]

    if not messagebox.askyesno(
        "Confirm Delete",
        f"Delete '{student}'?"
    ):
        return

    shutil.rmtree(
        os.path.join(
            STUDENT_FOLDER,
            student
        )
    )

    subprocess.run(
        [
            sys.executable,
            os.path.join(
                BASE_DIR,
                "encode_faces.py"
            )
        ]
    )

    load_students()

    student_info.configure(
        text="Student deleted successfully."
    )

# =====================================================
# BUTTONS
# =====================================================

button_frame = ctk.CTkFrame(app)

button_frame.pack(
    pady=20
)

ctk.CTkButton(
    button_frame,
    text="📝 Rename",
    width=170,
    command=rename_student
).grid(
    row=0,
    column=0,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="🗑 Delete",
    width=170,
    fg_color="red",
    hover_color="darkred",
    command=delete_student
).grid(
    row=0,
    column=1,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="🔄 Refresh",
    width=170,
    command=refresh_students
).grid(
    row=0,
    column=2,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="❌ Close",
    width=170,
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

load_students()

app.mainloop()