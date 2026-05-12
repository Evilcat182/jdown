import requests
import json
import time
import threading
import config
from pathlib import Path

from core import log, response_data, jdown_wait_ready, jdown_downloads_get_package_links, jdown_downloads_get_packages
from media import organize

PREFIX = "[DownloadWatch]"


def _is_finished(status: str) -> bool:
    if status is None:
        return False
    return status == "Finished" or status.startswith("Extraction OK")


def _all_links_finished(package_uuid: int) -> bool:
    links = jdown_downloads_get_package_links([package_uuid])
    if not links:
        return False
    return all(_is_finished(link.get("status") or "") for link in links)


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

            if _is_finished(status) and _all_links_finished(uid):
                reported_uuids.add(uid)
                save_to = pkg.get("saveTo")
                if save_to and Path(save_to).exists():
                    log(f"Finished: {name} ({save_to})", PREFIX)
                    organize(save_to)

        time.sleep(2)
