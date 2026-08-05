import json
import os

CONFIG_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "theme": "Dark",
    "voice_enabled": True,
    "voice_volume": 1.0,
    "voice_rate": 150,
    "recognition_threshold": 25.0,
    "camera_index": 0,
    "save_unknown_faces": True
}

class ConfigManager:
    _instance = None
    _settings = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self._settings = json.load(f)
            except Exception as e:
                print(f"[CONFIG] Error reading settings: {e}. Using defaults.")
                self._settings = DEFAULT_SETTINGS.copy()
        else:
            self._settings = DEFAULT_SETTINGS.copy()
            self.save()
            
        # Merge missing defaults if new keys were added
        modified = False
        for k, v in DEFAULT_SETTINGS.items():
            if k not in self._settings:
                self._settings[k] = v
                modified = True
        if modified:
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"[CONFIG] Error saving settings: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()

# Global instance
config = ConfigManager()
