import requests
import json
import time
import threading
from settings import API_BASE_URL, REQUEST_TIMEOUT_SECONDS
from functions import *

SETTLE_SECONDS = 4
PREFIX = "[AutoDownload]"

def jdown_linkgrabber_get_packages(name: str = None):
    query = {
        "availableOfflineCount"     : True,
        "availableOnlineCount"      : True,
        "availableTempUnknownCount" : True,
        "availableUnknownCount"     : True,
        "bytesTotal"                : True,
        "childCount"                : True,
        "comment"                   : True,
        "enabled"                   : True,
        "hosts"                     : True,
        "priority"                  : True,
        "saveTo"                    : True,
        "status"                    : True
    }
    ctx = "linkgrabberv2/queryPackages"
    try:
        res = requests.post(
            f"{API_BASE_URL}/{ctx}",
            params={"" : json.dumps(query)},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        error_log(f"Could not query linkgrabber packages: {exc}")
        return []
    packages = response_data(res, ctx, [])
    if name is not None:
        packages = [p for p in packages if name.lower() in p.get("name", "").lower()]
    return packages

def jdown_download_package(package_uuid: int) -> bool:
    """Move a linkgrabber package to the download list and start the download controller."""
    ctx = "linkgrabberv2/moveToDownloadlist"
    try:
        res = requests.post(
            f"{API_BASE_URL}/{ctx}",
            params={
                "linkIds": json.dumps([]),
                "packageIds": json.dumps([package_uuid]),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        error_log(f"Could not move package {package_uuid} to download list: {exc}")
        return False
    return response_data(res, ctx, False) == ''


def run(enabled: threading.Event):
    log("Starting linkgrabber watcher", PREFIX)
    seen_uuids: set[int] = set()
    # uid -> (last_bytesTotal, last_changed_time, ready_reported)
    pkg_state: dict[int, list] = {}

    while True:
        if not enabled.is_set():
            time.sleep(1)
            continue
        _= jdown_wait_ready()
        packages = jdown_linkgrabber_get_packages()
        now = time.time()
        for pkg in packages:
            uid = pkg.get("uuid")
            name = pkg.get("name", "?")
            total = pkg.get("bytesTotal", 0)

            if uid not in seen_uuids:
                seen_uuids.add(uid)
                pkg_state[uid] = [total, now, False]
                log(f"New Package found: {name}", PREFIX)
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
                    warning_log(f"Failed to start: {name}", PREFIX)

        time.sleep(2)