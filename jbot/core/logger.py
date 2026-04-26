import threading
from collections import deque
from datetime import datetime

from settings import DEBUG, COLOR_RESET, COLOR_GREY, COLOR_RED, COLOR_YELLOW, COLOR_GREEN

_log_lock = threading.Lock()
_log_counter = 0
_log_buffer: deque = deque(maxlen=500)


def get_logs(after: int = 0) -> list[dict]:
    with _log_lock:
        return [
            e for e in _log_buffer
            if e["id"] > after and (e["type"] != "debug" or DEBUG)
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
        if DEBUG:
            print(f"{COLOR_GREY}{p}{message}{COLOR_RESET}")
    elif type == "warning":
        print(f"{COLOR_YELLOW}{p}{message}{COLOR_RESET}")
    elif type == "error":
        print(f"{COLOR_RED}{p}ERROR: {message}{COLOR_RESET}")
    elif type == "success":
        print(f"{COLOR_GREEN}{p}{message}{COLOR_RESET}")
    else:
        print(f"{p}{message}")
