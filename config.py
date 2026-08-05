import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(
    BASE_DIR,
    "settings.json"
)

DEFAULT_SETTINGS = {

    "theme":"Dark",

    "voice":True,

    "threshold":0.65,

    "camera":0

}


def load_settings():

    if not os.path.exists(
        SETTINGS_FILE
    ):

        save_settings(DEFAULT_SETTINGS)

        return DEFAULT_SETTINGS

    try:

        with open(
            SETTINGS_FILE,
            "r"
        ) as f:

            return json.load(f)

    except:

        save_settings(DEFAULT_SETTINGS)

        return DEFAULT_SETTINGS


def save_settings(data):

    with open(
        SETTINGS_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )


settings = load_settings()