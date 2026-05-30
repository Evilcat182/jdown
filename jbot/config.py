from pathlib import Path
import threading
from core.logger import log
import json
import os

CONFIG_JSON_PATH = "/config/jbot.json"
_PREFIX = "[CONFIG]"

_path = Path(CONFIG_JSON_PATH)

_SCHEMA = {
    # ── Automation toggles ──────────────────────────────────────────────────
    "linkgrabber":              {"default": True,  "env": "AUTOSTART_DOWNLOADS",    "type": bool, "ui": True, "event": True},
    "downloads":                {"default": True,  "env": "AUTOORGANIZE_DOWNLOADS", "type": bool, "ui": True, "event": True},
    "plex":                     {"default": True,  "env": "PLEX_SCAN_ENABLED",      "type": bool, "ui": True, "event": True},
    "delete_source":            {"default": False, "env": "DELETE_SOURCE",          "type": bool, "ui": True, "event": True},
    "dialogs":                  {"default": True,  "env": "AUTOANSWER_DIALOGS",     "type": bool, "ui": True, "event": True},

    # ── Paths ───────────────────────────────────────────────────────────────
    "scan_path":                {"default": "/output",      "env": "SCAN_PATH",          "type": str, "ui": False},
    "downloads_path":           {"default": "/output",      "env": "DOWNLOADS_PATH",     "type": str, "ui": False},
    "movie_destination":        {"default": "/data/movies", "env": "MOVIE_DESTINATION",  "type": str, "ui": False},
    "series_destination":       {"default": "/data/series", "env": "SERIES_DESTINATION", "type": str, "ui": False},

    # ── Plex ────────────────────────────────────────────────────────────────
    "plex_api_root":            {"default": "", "env": "PLEX_API_ROOT",       "type": str, "ui": True},
    "plex_token":               {"default": "", "env": "PLEX_TOKEN",          "type": str, "ui": False},  # secret
    "plex_movie_lib_name":      {"default": "", "env": "PLEX_MOVIE_LIB_NAME", "type": str, "ui": True},
    "plex_show_lib_name":       {"default": "", "env": "PLEX_SHOW_LIB_NAME",  "type": str, "ui": True},

    # ── Organizer templates ─────────────────────────────────────────────────
    "movie_settings": {
        "default": {
            "folder_template_name": "{title} {year_in_brackets}",
            "file_template_name":   "{dotted_title}.{year}.{video_codec}.{screen_size}",
            "mandatory": ["title", "dotted_title", "year", "video_codec", "screen_size"],
        },
        "env": None, "type": dict, "ui": True,
    },
    "series_settings": {
        "default": {
            "folder_template_name":         "{title} {year_in_brackets}",
            "file_template_name":           "{dotted_title}.{season_and_episode}.{dotted_episode_title}.{video_codec}.{screen_size}",
            "episode_folder_template_name": "{dotted_title}.{season_and_episode}.{dotted_episode_title}.{video_codec}.{screen_size}",
            "mandatory": ["title", "dotted_title", "season_and_episode", "video_codec", "screen_size"],
        },
        "env": None, "type": dict, "ui": True,
    },
    "organizer_excludes": {
        "default": [
            {"Pattern": "*.nfo",        "Dir": False, "CS": False},
            {"Pattern": "*.jpg",        "Dir": False, "CS": False},
            {"Pattern": "*.txt",        "Dir": False, "CS": False},
            {"Pattern": "*.url",        "Dir": False, "CS": False},
            {"Pattern": "*.iso",        "Dir": False, "CS": False},
            {"Pattern": "*-sample.*",   "Dir": False, "CS": False},
            {"Pattern": "sample.*",     "Dir": False, "CS": False},
            {"Pattern": "proof",        "Dir": True,  "CS": False},
            {"Pattern": "sample",       "Dir": True,  "CS": False},
        ],
        "env": None, "type": list, "ui": True
    },
    "video_extensions":         {"default": [".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv"],        "env": "VIDEO_EXTENSIONS",         "type": list, "ui": True},
    "media_confidence_fields":  {"default": ["screen_size", "source", "video_codec", "audio_codec"], "env": "MEDIA_CONFIDENCE_FIELDS",  "type": list, "ui": True},

    # ── Internal / secrets (env-only, not shown in UI) ──────────────────────
    "api_base_url":             {"default": "http://gluetun:3128", "env": "API_BASE_URL",             "type": str,  "ui": False},
    "debug":                    {"default": False,                 "env": "DEBUG",                    "type": bool, "ui": False},
    "extraction_passwords":     {"default": "",                    "env": "EXTRACTION_PASSWORDS",     "type": str,  "ui": False},
    "premium_account_hoster":   {"default": "",                    "env": "PREMIUM_ACCOUNT_HOSTER",   "type": str,  "ui": False},
    "premium_account_username": {"default": "",                    "env": "PREMIUM_ACCOUNT_USERNAME", "type": str,  "ui": False},
    "premium_account_password": {"default": "",                    "env": "PREMIUM_ACCOUNT_PASSWORD", "type": str,  "ui": False},
    "request_timeout_seconds":  {"default": 10,                    "env": "REQUEST_TIMEOUT_SECONDS",  "type": int,  "ui": False},
    "wait_timeout_seconds":     {"default": 120,                   "env": "WAIT_TIMEOUT_SECONDS",     "type": int, "ui": False},
}

_EVENTS: dict[str: threading.Event] = {}
for key, val in _SCHEMA.items():
    if val.get("event"):
        _EVENTS[key] = threading.Event()

# The live config values
_store: dict = {}

def _save():
    json_data = json.dumps(_store,indent=2)
    _path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _path.parent / f"_{_path.name}"
    tmp_path.write_text(json_data)
    os.replace(tmp_path,_path)
    log(f"Config saved to {_path}", _PREFIX, "debug")

def _load_file() -> dict:
    if not _path.exists():
        log(f"No config file at {_path}, using defaults", _PREFIX, "debug")
        return {}
    try:
        return json.loads(_path.read_text())
    except Exception as exc:
        log(f"Could not read {_path}: {exc}", _PREFIX, "error")
        return {}

def _apply_to_event(key: str, value: bool):
    ev = _EVENTS.get(key)
    if ev is None:
        return
    ev.set() if value else ev.clear()

def _convert_str_to_bool(string:str) -> bool:
    return string.lower().strip() in ["1","true","yes"]

def _convert_type(key: str, value) -> object:
    wanted_type = _SCHEMA.get(key).get("type")
    if wanted_type is bool:
        return _convert_str_to_bool(str(value))
    return value
        

# Load default values
for key, val in _SCHEMA.items():
    _store[key] = val.get("default")

# Load values from settings file
file_data = _load_file()
for key in _SCHEMA.keys():
    if key in file_data:
        newval = _convert_type(key,file_data.get(key))
        if _store.get(key) != newval:
            log(f"Config '{key}' overwritten by file to '{newval}'",_PREFIX, "debug")
            _store[key] = newval

# Load values from env var if set
for key, val in _SCHEMA.items():
    if val.get("env") is not None:
        env = os.getenv(val.get("env"))
        if env is not None:
            newval = _convert_type(key,env)
            if _store.get(key) != newval:
                log(f"Config '{key}' overwritten by env var to '{newval}'",_PREFIX, "debug")
                _store[key] = newval

# sync events to final val
for key, val in _EVENTS.items():
    if _store.get(key):
        _EVENTS.get(key).set()

_save()

def get_config(key: str):
    return _store.get(key)

def get_event(key: str) -> threading.Event | None:
    return _EVENTS.get(key)

def get_state():
    result = {}
    for key, ev in _EVENTS.items():
        result[key] = ev.is_set()
    return result

def get_ui_values() -> dict:
    result = {}
    for key,val in _SCHEMA.items():
        if val.get("ui"):
            result[key] = _store.get(key)
    return result

def set_config(key: str, value, save=True):
    """Update one value, sync its event, persist to file."""
    if key not in _SCHEMA:
        raise KeyError(key)
    conv_val = _convert_type(key,value)
    _store[key] = conv_val
    _apply_to_event(key, conv_val)
    if save:
        _save()

def patch_config(updates: dict):
    """Update multiple values atomically, then save once."""
    for key, val in updates.items():
        set_config(key, val, False)
    _save()

