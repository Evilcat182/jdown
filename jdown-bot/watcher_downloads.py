import requests
from pathlib import Path
import json
import time
from settings import API_BASE_URL, REQUEST_TIMEOUT_SECONDS
from functions import *
from organizer import organize

def jdown_downloads_get_packages(name: str = None):
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
    ctx = "downloadsV2/queryPackages"
    try:
        res = requests.post(
            f"{API_BASE_URL}/{ctx}",
            params={"" : json.dumps(query)},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        error_log(f"Could not query download packages: {exc}")
        return []
    packages = response_data(res, ctx, [])
    if name is not None:
        packages = [p for p in packages if name.lower() in p.get("name", "").lower()]
    return packages

def jdown_downloads_get_package_links(package_uuid: list[int]):
    query = {
        "addedDate"        : True,
        "bytesLoaded"      : True,
        "bytesTotal"       : True,
        "comment"          : True,
        "enabled"          : True,
        "eta"              : True,
        "extractionStatus" : True,
        "finished"         : True,
        "finishedDate"     : True,
        "host"             : True,
        #"jobUUIDs"         : (long[]),
        "maxResults"       : -1,
        "packageUUIDs"     : package_uuid,
        "password"         : True,
        "priority"         : True,
        "running"          : True,
        "skipped"          : True,
        "speed"            : True,
        "startAt"          : 0,
        "status"           : True,
        "url"              : True
    }
    ctx = "downloadsV2/queryLinks"
    try:
        res = requests.post(
            f"{API_BASE_URL}/{ctx}",
            params={"" : json.dumps(query)},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        error_log(f"Could not query download links: {exc}")
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


PREFIX = "[DownloadWatch]"

reported_uuids: set[int] = set()

while True:
    _ = jdown_wait_ready()
    packages = jdown_downloads_get_packages()
    for pkg in packages:
        uid = pkg.get("uuid")
        name = pkg.get("name", "?")
        status = pkg.get("status") or ""

        if uid in reported_uuids:
            continue

        if _is_finished(status) and _all_links_finished(uid):
            reported_uuids.add(uid)
            if Path(pkg.get('saveTo')).exists():
                print(f"{PREFIX} Finished: {name} ({pkg.get('saveTo', '?')})")
                organize(pkg.get('saveTo'))

    time.sleep(2)

#while True:
#    time.sleep(1)
#    allpkgs = jdown_downloads_get_packages()
#    if not allpkgs:
#        continue
#    pkg = jdown_downloads_get_packages()[0]
#    link = jdown_downloads_get_package_links([pkg["uuid"]])[0]
#    print(f"Package: {pkg["status"]}")
#    print(f"Link: {link["status"]}")
#    print("")
  