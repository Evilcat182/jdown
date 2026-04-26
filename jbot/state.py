import threading
import os
from pathlib import Path
import json
from core import log

CONFIG_JSON_PATH = "/config/jbot.json"
path = Path(CONFIG_JSON_PATH)

_EVENTS = {
    "linkgrabber":   (threading.Event(), "AUTOSTART_DOWNLOADS",     True),
    "downloads":     (threading.Event(), "AUTOORGANIZE_DOWNLOADS",  True),
    "plex":          (threading.Event(), "PLEX_SCAN_ENABLED",       True),
    "delete_source": (threading.Event(), "DELETE_SOURCE",           False),
    "dialogs":       (threading.Event(), "AUTOANSWER_DIALOGS",      True),
}

def get_event(name: str) -> threading.Event | None:
    entry = _EVENTS.get(name)
    return entry[0] if entry else None

def get_state() -> dict:
    return {key: ev.is_set() for key, (ev, _, _d) in _EVENTS.items()}

def save_state():
    json_content = json.dumps(get_state(), indent=2)
    tmp_path = path.parent / f"_{path.name}"
    tmp_path.write_text(json_content)
    os.replace(tmp_path, path)
    log(f"State saved to {path}", "[State]", "debug")

def load_state():
    if not path.exists():
        log(f"No state file found at {path}, using defaults", "[State]", "debug")
        return
    data = json.loads(path.read_text())
    for key, (ev, _, _d) in _EVENTS.items():
        ev.set() if data.get(key) else ev.clear()
    log(f"State loaded from {path}: {data}", "[State]", "debug")

# 1. Apply defaults
for ev, _, default in _EVENTS.values():
    ev.set() if default else ev.clear()

# 2. File overrides defaults
load_state()

# 3. Explicit env vars override file
for ev, env_var, _ in _EVENTS.values():
    val = os.getenv(env_var)
    if val is not None:
        ev.set() if val == "1" else ev.clear()