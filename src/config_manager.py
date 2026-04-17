import json
import os

CONFIG_PATH = os.path.expanduser("~/.config/ibus-lekhika/config.json")
DEFAULT_CONFIG = {
    "smart_correction": True,
    "auto_correct": True,
    "indic_numbers": True,
    "symbols_translit": True,
    "space_commits_suggestion": True,
    "enable_suggestions": True,
    "dictionary_path": os.path.expanduser("~/.local/share/lekhika-core/lekhikadict.akshardb")
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Merge with defaults to handle missing keys
            return {**DEFAULT_CONFIG, **config}
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
