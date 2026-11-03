import time
import threading
from pathlib import Path

from core import log, jdown_wait_ready, jdown_downloads_get_packages, jdown_package_is_finished
from media import organize

PREFIX = "[DownloadWatch]"


def _check_packages(reported_uuids: set[int]):
    packages = jdown_downloads_get_packages()
    for pkg in packages:
        uid = pkg.get("uuid")
        name = pkg.get("name", "?")
        status = pkg.get("status") or ""

        if uid in reported_uuids:
            continue

        if jdown_package_is_finished(uid, status):
            # Mark first so a failing organize() is not retried every loop
            reported_uuids.add(uid)
            save_to = pkg.get("saveTo")
            if save_to and Path(save_to).exists():
                log(f"Finished: {name} ({save_to})", PREFIX)
                try:
                    organize(save_to)
                except Exception as exc:
                    log(f"Organizing '{name}' failed: {exc}", PREFIX, "error")


def run(enabled: threading.Event):
    log("Starting downloads watcher", PREFIX)
    reported_uuids: set[int] = set()

    while True:
        if not enabled.is_set():
            time.sleep(1)
            continue
        try:
            jdown_wait_ready()
            _check_packages(reported_uuids)
        except Exception as exc:
            log(f"Unexpected error: {exc}", PREFIX, "error")
        time.sleep(2)
