import requests
import json
import time
import threading
import config
from core import log, response_data, jdown_wait_ready, jdown_linkgrabber_get_packages, jdown_download_package

PREFIX = "[AutoDownload]"
SETTLE_SECONDS = 4


def run(enabled: threading.Event):
    log("Starting linkgrabber watcher", PREFIX)
    seen_uuids: set[int] = set()
    # uid -> [last_bytesTotal, last_changed_time, ready_reported]
    pkg_state: dict[int, list] = {}

    while True:
        if not enabled.is_set():
            time.sleep(1)
            continue
        jdown_wait_ready()
        packages = jdown_linkgrabber_get_packages()
        now = time.time()
        for pkg in packages:
            uid = pkg.get("uuid")
            name = pkg.get("name", "?")
            total = pkg.get("bytesTotal", 0)

            if uid not in seen_uuids:
                seen_uuids.add(uid)
                pkg_state[uid] = [total, now, False]
                log(f"New package found: {name}", PREFIX)
                continue

            last_total, last_changed, ready = pkg_state[uid]
            if total != last_total:
                pkg_state[uid] = [total, now, False]
            elif not ready and (now - last_changed) >= SETTLE_SECONDS:
                pkg_state[uid][2] = True
                log(f"Package ready: {name} ({total} bytes)", PREFIX)
                ok = jdown_download_package(uid)
                if ok:
                    log(f"Download started: {name}", PREFIX)
                else:
                    log(f"Failed to start: {name}", PREFIX, "warning")

        time.sleep(2)
