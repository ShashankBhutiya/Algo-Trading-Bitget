import json
import threading
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/bot_config.json")
_lock = threading.Lock()

def load_config():
    with _lock:
        if not os.path.exists(CONFIG_PATH):
            return {}
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

def update_config(new_data):
    with _lock:
        config = load_config()
        config.update(new_data)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        return config
