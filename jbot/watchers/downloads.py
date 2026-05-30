import requests
import json
import time
import threading
import config
from pathlib import Path

from core import log, response_data, jdown_wait_ready, jdown_downloads_get_packages, jdown_package_is_finished
from media import organize

PREFIX = "[DownloadWatch]"


def run(enabled: threading.Event):
    log("Starting downloads watcher", PREFIX)
    reported_uuids: set[int] = set()

    while True:
        if not enabled.is_set():
            time.sleep(1)
            continue
        jdown_wait_ready()
        packages = jdown_downloads_get_packages()
        for pkg in packages:
            uid = pkg.get("uuid")
            name = pkg.get("name", "?")
            status = pkg.get("status") or ""

            if uid in reported_uuids:
                continue

            if jdown_package_is_finished(uid, status):
                reported_uuids.add(uid)
                save_to = pkg.get("saveTo")
                if save_to and Path(save_to).exists():
                    log(f"Finished: {name} ({save_to})", PREFIX)
                    organize(save_to)

        time.sleep(2)
