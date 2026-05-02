import requests
import json
import time
import threading
import config
from pathlib import Path

from core import log, response_data, jdown_wait_ready
from media import organize

PREFIX = "[DownloadWatch]"


def jdown_downloads_get_state():
    # returned states: STOPPED_STATE, RUNNING, PAUSE
    ctx = "downloadcontroller/getCurrentState"
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/{ctx}",
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not get downloads state: {exc}", PREFIX, "error")
        return None
    return response_data(res, ctx, None)


def jdown_downloads_get_packages(name: str = None):
    query = {
        "availableOfflineCount":      True,
        "availableOnlineCount":       True,
        "availableTempUnknownCount":  True,
        "availableUnknownCount":      True,
        "bytesTotal":                 True,
        "childCount":                 True,
        "comment":                    True,
        "enabled":                    True,
        "hosts":                      True,
        "priority":                   True,
        "saveTo":                     True,
        "status":                     True,
    }
    ctx = "downloadsV2/queryPackages"
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/{ctx}",
            params={"": json.dumps(query)},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not query download packages: {exc}", PREFIX, "error")
        return []
    packages = response_data(res, ctx, [])
    if name is not None:
        packages = [p for p in packages if name.lower() in p.get("name", "").lower()]
    return packages


def jdown_downloads_get_package_links(package_uuid: list[int]):
    query = {
        "addedDate":       True,
        "bytesLoaded":     True,
        "bytesTotal":      True,
        "comment":         True,
        "enabled":         True,
        "eta":             True,
        "extractionStatus": True,
        "finished":        True,
        "finishedDate":    True,
        "host":            True,
        "maxResults":      -1,
        "packageUUIDs":    package_uuid,
        "password":        True,
        "priority":        True,
        "running":         True,
        "skipped":         True,
        "speed":           True,
        "startAt":         0,
        "status":          True,
        "url":             True,
    }
    ctx = "downloadsV2/queryLinks"
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/{ctx}",
            params={"": json.dumps(query)},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not query download links: {exc}", PREFIX, "error")
        return []
    return response_data(res, ctx, [])


def jdown_get_archive_info(link_ids: list[int] = None, package_ids: list[int] = None) -> list:
    ctx = "extraction/getArchiveInfo"
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/{ctx}",
            params={
                "linkIds":    json.dumps(link_ids or []),
                "packageIds": json.dumps(package_ids or []),
            },
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not get archive info: {exc}", PREFIX, "error")
        return []
    return response_data(res, ctx, [])


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
