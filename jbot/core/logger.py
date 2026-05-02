import os
import threading
from collections import deque
from datetime import datetime

COLOR_RESET  = "\033[0m"
COLOR_GREY   = "\033[90m"
COLOR_RED    = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN  = "\033[32m"

def _is_debug() -> bool:
    return os.getenv("DEBUG", "").lower().strip() in ("1", "true", "yes")

_log_lock = threading.Lock()
_log_counter = 0
_log_buffer: deque = deque(maxlen=500)


def get_logs(after: int = 0) -> list[dict]:
    with _log_lock:
        return [
            e for e in _log_buffer
            if e["id"] > after and (e["type"] != "debug" or _is_debug())
        ]


def log(message: str, prefix: str = "", type: str = None):
    global _log_counter
    p = f"{prefix} " if prefix else ""

    with _log_lock:
        _log_counter += 1
        _log_buffer.append({
            "id":      _log_counter,
            "ts":      datetime.now().strftime("%H:%M:%S"),
            "type":    type or "info",
            "prefix":  prefix,
            "message": message,
        })

    if type == "debug":
        if _is_debug():
            print(f"{COLOR_GREY}{p}{message}{COLOR_RESET}")
    elif type == "warning":
        print(f"{COLOR_YELLOW}{p}{message}{COLOR_RESET}")
    elif type == "error":
        print(f"{COLOR_RED}{p}ERROR: {message}{COLOR_RESET}")
    elif type == "success":
        print(f"{COLOR_GREEN}{p}{message}{COLOR_RESET}")
    else:
        print(f"{p}{message}")
