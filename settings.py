import customtkinter as ctk
import json
import os
import pyttsx3
from utils import center_window
from tkinter import messagebox

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(
    BASE_DIR,
    "settings.json"
)

# =====================================================
# DEFAULT SETTINGS
# =====================================================

DEFAULT_SETTINGS = {

    "theme": "Dark",

    "voice": True,

    "threshold": 0.65,

    "camera": 0

}

# =====================================================
# LOAD SETTINGS
# =====================================================

def load_settings():

    if not os.path.exists(
        SETTINGS_FILE
    ):

        return DEFAULT_SETTINGS.copy()

    try:

        with open(
            SETTINGS_FILE,
            "r"
        ) as f:

            data = json.load(f)

        for key, value in DEFAULT_SETTINGS.items():

            if key not in data:

                data[key] = value

        return data

    except:

        return DEFAULT_SETTINGS.copy()


settings = load_settings()

# =====================================================
# THEME
# =====================================================

ctk.set_appearance_mode(
    settings["theme"].lower()
)

ctk.set_default_color_theme(
    "blue"
)

# =====================================================
# WINDOW
# =====================================================

app = ctk.CTk()

app.title(
    "Smart Attendance Settings"
)
app.resizable(
    False,
    False
)
center_window(app, 550, 520)

# =====================================================
# TITLE
# =====================================================

title = ctk.CTkLabel(

    app,

    text="⚙ Smart Attendance Settings",

    font=("Arial",28,"bold")

)

title.pack(
    pady=20
)
# =====================================================
# THEME
# =====================================================

theme_label = ctk.CTkLabel(
    app,
    text="🎨 Theme",
    font=("Arial",16,"bold")
)

theme_label.pack(pady=(15,5))

theme_option = ctk.CTkOptionMenu(
    app,
    values=[
        "Dark",
        "Light"
    ]
)

theme_option.pack()

theme_option.set(
    settings["theme"]
)

# =====================================================
# VOICE
# =====================================================

voice_var = ctk.BooleanVar(
    value=settings["voice"]
)

voice_switch = ctk.CTkSwitch(
    app,
    text="Enable Voice",
    variable=voice_var
)

voice_switch.pack(
    pady=20
)

# =====================================================
# TEST VOICE
# =====================================================

def test_voice():

    try:

        engine = pyttsx3.init()

        engine.setProperty("rate",170)

        engine.setProperty("volume",1)

        engine.say(
            "Voice settings are working correctly."
        )

        engine.runAndWait()

    except Exception as e:

        messagebox.showerror(
            "Voice Error",
            str(e)
        )

ctk.CTkButton(
    app,
    text="🔊 Test Voice",
    width=220,
    command=test_voice
).pack(pady=10)

# =====================================================
# THRESHOLD
# =====================================================

threshold_label = ctk.CTkLabel(
    app,
    text="Recognition Threshold",
    font=("Arial",16,"bold")
)

threshold_label.pack(
    pady=(20,5)
)

threshold_slider = ctk.CTkSlider(
    app,
    from_=0.40,
    to=0.90
)

threshold_slider.pack(
    fill="x",
    padx=40
)

threshold_slider.set(
    settings["threshold"]
)

threshold_value = ctk.CTkLabel(
    app,
    text=f"{settings['threshold']:.2f}"
)

threshold_value.pack()

def update_threshold(value):

    threshold_value.configure(
        text=f"{float(value):.2f}"
    )

threshold_slider.configure(
    command=update_threshold
)

# =====================================================
# CAMERA
# =====================================================

camera_label = ctk.CTkLabel(
    app,
    text="📷 Camera Index",
    font=("Arial",16,"bold")
)

camera_label.pack(
    pady=(20,5)
)

camera_entry = ctk.CTkEntry(
    app,
    width=150
)

camera_entry.pack()

camera_entry.insert(
    0,
    str(settings["camera"])
)
# =====================================================
# SAVE SETTINGS
# =====================================================

def save_settings():

    try:

        camera = int(
            camera_entry.get()
        )

    except:

        messagebox.showerror(
            "Invalid Camera",
            "Camera index must be a number."
        )

        return

    data = {

        "theme": theme_option.get(),

        "voice": voice_var.get(),

        "threshold": round(
            float(
                threshold_slider.get()
            ),
            2
        ),

        "camera": camera

    }

    try:

        with open(
            SETTINGS_FILE,
            "w"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

        ctk.set_appearance_mode(
            data["theme"].lower()
        )

        messagebox.showinfo(
            "Success",
            "Settings saved successfully.\n\nRestart the application to apply all changes."
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )


# =====================================================
# RESET SETTINGS
# =====================================================

def reset_settings():

    try:

        with open(
            SETTINGS_FILE,
            "w"
        ) as f:

            json.dump(
                DEFAULT_SETTINGS,
                f,
                indent=4
            )

        messagebox.showinfo(
            "Reset",
            "Default settings restored."
        )

        app.destroy()

    except Exception as e:

        messagebox.showerror(
            "Error",
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
    text="💾 Save Settings",
    width=180,
    height=45,
    command=save_settings
).grid(
    row=0,
    column=0,
    padx=10
)

ctk.CTkButton(
    button_frame,
    text="↺ Reset Default",
    width=180,
    height=45,
    fg_color="orange",
    hover_color="#cc8400",
    command=reset_settings
).grid(
    row=0,
    column=1,
    padx=10
)

# =====================================================
# CLOSE WINDOW
# =====================================================

def close_window():

    app.destroy()

app.protocol(
    "WM_DELETE_WINDOW",
    close_window
)

# =====================================================
# RUN
# =====================================================

app.mainloop()