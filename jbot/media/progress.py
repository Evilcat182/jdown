"""Thread-safe registry of in-progress organize copy jobs.

Used to report byte-based copy progress to the WebUI while an
organize() call is running in another thread (e.g. the Flask request
thread or a watcher thread).
"""

import threading

_LOCK = threading.Lock()
_JOBS: dict[str, dict] = {}


def start_job(key: str, name: str, total_bytes: int) -> None:
    with _LOCK:
        _JOBS[key] = {
            "name": name,
            "total_bytes": total_bytes,
            "copied_bytes": 0,
        }


def update_job(key: str, bytes_delta: int) -> None:
    with _LOCK:
        job = _JOBS.get(key)
        if job is not None:
            job["copied_bytes"] += bytes_delta


def finish_job(key: str) -> None:
    with _LOCK:
        _JOBS.pop(key, None)


def get_job(key: str) -> dict | None:
    with _LOCK:
        job = _JOBS.get(key)
        return dict(job) if job is not None else None


def get_all_jobs() -> dict[str, dict]:
    """Return a snapshot of all active copy jobs, keyed by source path."""
    with _LOCK:
        return {k: dict(v) for k, v in _JOBS.items()}
