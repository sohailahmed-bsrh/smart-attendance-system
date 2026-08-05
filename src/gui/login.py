import customtkinter as ctk
from tkinter import messagebox
from src.core.voice_engine import voice
import time

class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, corner_radius=0)
        self.master = master
        self.on_login_success = on_login_success
        self.pack(fill="both", expand=True)
        
        self.configure(fg_color=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]))
        
        self._setup_ui()

    def _setup_ui(self):
        # Create a centered container
        self.container = ctk.CTkFrame(self, width=400, height=500, corner_radius=15)
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.container.pack_propagate(False)
        
        # Logo / Icon
        ctk.CTkLabel(self.container, text="🔐", font=("Arial", 60)).pack(pady=(40, 10))
        
        # Title
        ctk.CTkLabel(self.container, text="Welcome Back", font=("Arial", 28, "bold")).pack(pady=(0, 5))
        ctk.CTkLabel(self.container, text="Sign in to continue", font=("Arial", 14), text_color="gray").pack(pady=(0, 30))
        
        # Username
        self.entry_username = ctk.CTkEntry(self.container, width=300, height=45, placeholder_text="Username", font=("Arial", 14))
        self.entry_username.pack(pady=(0, 15))
        
        # Password
        self.entry_password = ctk.CTkEntry(self.container, width=300, height=45, placeholder_text="Password", show="•", font=("Arial", 14))
        self.entry_password.pack(pady=(0, 15))
        
        # Remember Me
        self.chk_remember = ctk.CTkCheckBox(self.container, text="Remember Me", font=("Arial", 12))
        self.chk_remember.pack(anchor="w", padx=50, pady=(0, 25))
        
        # Login Button
        self.btn_login = ctk.CTkButton(self.container, text="Login", width=300, height=45, font=("Arial", 16, "bold"), command=self._handle_login)
        self.btn_login.pack(pady=(0, 20))
        
        # Error Label
        self.lbl_error = ctk.CTkLabel(self.container, text="", font=("Arial", 12), text_color="red")
        self.lbl_error.pack()
        
        # Bind Enter key to login
        self.master.bind('<Return>', lambda event: self._handle_login())

    def _handle_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        
        if not username or not password:
            self.lbl_error.configure(text="Please enter username and password")
            return
            
        self.btn_login.configure(state="disabled", text="Authenticating...")
        self.lbl_error.configure(text="")
        
        # Simulate network/auth delay for professional feel
        self.after(800, self._verify_credentials, username, password)

    def _verify_credentials(self, username, password):
        # Admin authentication
        if username.lower() == "admin" and password == "admin":
            self.lbl_error.configure(text="Login successful!", text_color="green")
            voice.speak("Login successful. Welcome Administrator.")
            
            # Transition
            self.after(500, self._finish_login)
        else:
            self.lbl_error.configure(text="Invalid credentials", text_color="red")
            self.btn_login.configure(state="normal", text="Login")
            voice.speak("Invalid credentials. Please try again.")
            
    def _finish_login(self):
        self.master.unbind('<Return>')
        self.destroy()
        self.on_login_success()
