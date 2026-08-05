import customtkinter as ctk
from tkinter import messagebox
import subprocess
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Smart Attendance System - Login")
app.geometry("500x500")
app.resizable(False, False)

title = ctk.CTkLabel(
    app,
    text="SMART ATTENDANCE SYSTEM",
    font=("Arial", 28, "bold")
)
title.pack(pady=(40, 10))

subtitle = ctk.CTkLabel(
    app,
    text="Administrator Login",
    font=("Arial", 18)
)
subtitle.pack(pady=(0, 30))

username_entry = ctk.CTkEntry(
    app,
    width=300,
    height=40,
    placeholder_text="Username"
)
username_entry.pack(pady=10)

password_entry = ctk.CTkEntry(
    app,
    width=300,
    height=40,
    placeholder_text="Password",
    show="*"
)
password_entry.pack(pady=10)


def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username == "admin" and password == "12345":
        app.destroy()
        subprocess.Popen([sys.executable, "gui.py"])
    else:
        messagebox.showerror(
            "Login Failed",
            "Invalid Username or Password!"
        )


def clear_fields():
    username_entry.delete(0, "end")
    password_entry.delete(0, "end")


login_btn = ctk.CTkButton(
    app,
    text="Login",
    width=300,
    height=45,
    command=login
)
login_btn.pack(pady=15)

clear_btn = ctk.CTkButton(
    app,
    text="Clear",
    width=300,
    height=45,
    fg_color="orange",
    hover_color="#cc8400",
    command=clear_fields
)
clear_btn.pack(pady=10)

exit_btn = ctk.CTkButton(
    app,
    text="Exit",
    width=300,
    height=45,
    fg_color="red",
    hover_color="darkred",
    command=app.destroy
)
exit_btn.pack(pady=10)

app.bind("<Return>", lambda event: login())

app.mainloop()