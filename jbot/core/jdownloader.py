import requests
import json
import time
import config
from .logger import log

PREFIX = "[JDownloader]"

_PACKAGES_QUERY = {
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

_DOWNLOAD_STATUS_QUERY = {
    "bytesLoaded":  True,
    "bytesTotal":   True,
    "childCount":   True,
    "enabled":      True,
    "eta":          True,
    "finished":     True,
    "name":         True,
    "running":      True,
    "saveTo":       True,
    "speed":        True,
    "status":       True,
}

def response_data(res: requests.Response, context: str, default):
    if res.status_code != 200:
        log(f"{context} returned HTTP {res.status_code}: {res.text}", PREFIX, "debug")
        return default
    try:
        body = res.json()
    except ValueError:
        log(f"{context} returned invalid JSON: {res.text}", PREFIX, "debug")
        return default
    if "data" not in body:
        log(f"{context} response has no 'data' key: {body}", PREFIX, "debug")
        return default
    return body["data"]


def jdown_is_ready() -> bool:
    try:
        res = requests.get(f"{config.get_config("api_base_url")}/jd/version", timeout=config.get_config("request_timeout_seconds"))
    except requests.RequestException as exc:
        log(f"Could not reach JDownloader API: {exc}", PREFIX, "debug")
        return False
    return res.status_code == 200


def jdown_wait_ready(timeout_seconds: int = config.get_config("wait_timeout_seconds")) -> bool:
    start = time.time()
    while not jdown_is_ready():
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for JDownloader to become ready", PREFIX, "error")
            return False
        time.sleep(1)
    return True


def jdown_wait_not_ready(timeout_seconds: int = config.get_config("wait_timeout_seconds")) -> bool:
    start = time.time()
    while jdown_is_ready():
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for JDownloader to go down", PREFIX, "error")
            return False
        time.sleep(1)
    return True


def jdown_list_dialogs() -> list:
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/dialogs/list",
            timeout=config.get_config("request_timeout_seconds")
        )
    except requests.RequestException as exc:
        log(f"While listing dialogs: {exc}", PREFIX, "error")
        return []
    data = response_data(res, "dialogs/list", [])
    return data if isinstance(data, list) else []


def jdown_wait_for_dialog(timeout_seconds: int = config.get_config("wait_timeout_seconds")) -> list:
    log(f"Waiting for install dialog (timeout={timeout_seconds}s)", PREFIX, "debug")
    start = time.time()
    while True:
        dialogs = jdown_list_dialogs()
        if dialogs:
            log(f"Dialog(s) detected: {dialogs}", PREFIX, "debug")
            return dialogs
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for install dialog", PREFIX, "error")
            return []
        time.sleep(1)


def jdown_config_set(interface_name: str, storage: str, key: str, value: object) -> bool:
    log(
        f"Setting config interface='{interface_name}' storage='{storage}' key='{key}' value='{value}'",
        PREFIX, "debug"
    )
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/config/set",
            params=[
                ("", interface_name),
                ("", storage),
                ("", key),
                ("", value)
            ],
            timeout=config.get_config("request_timeout_seconds")
        )
    except requests.RequestException as exc:
        log(f"Could not set config '{interface_name}': {exc}", PREFIX, "error")
        return False
    return bool(response_data(res, "config/set", False))


def jdown_get_dialog(dialog_id: int) -> dict | None:
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/dialogs/get",
            params={"id": dialog_id, "icon": "false", "properties": "true"},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"While getting dialog {dialog_id}: {exc}", PREFIX, "error")
        return None
    return response_data(res, "dialogs/get", None)


def jdown_get_dialog_type_info(dialog_type: str) -> dict | None:
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/dialogs/getTypeInfo",
            params={"dialogType": dialog_type},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"While getting type info: {exc}", PREFIX, "error")
        return None
    return response_data(res, "dialogs/getTypeInfo", None)


def jdown_answer_dialog(dialog_id: int, data: dict, dialog_type: str = "") -> bool:
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/dialogs/answer",
            params={"id": dialog_id, "data": json.dumps(data)},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"While answering dialog {dialog_id}: {exc}", PREFIX, "error")
        return False
    if res.status_code != 200:
        log(f"Answer dialog {dialog_id} failed: {res.status_code} {res.text}", PREFIX, "error")
        if dialog_type:
            type_info = jdown_get_dialog_type_info(dialog_type)
            if type_info:
                log(f"Expected answer schema (in) for '{dialog_type}': {type_info.get('in')}", PREFIX, "error")
                log(f"Dialog output schema (out) for '{dialog_type}': {type_info.get('out')}", PREFIX, "error")
        return False
    log(f"Dialog {dialog_id} answered and closed (type={dialog_type})", PREFIX)
    return True


def jdown_archivepassword_add(password: str) -> bool:
    log(f"Adding archive password (len={len(password)})", PREFIX, "debug")
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/extraction/addArchivePassword",
            params={"":password},
            timeout=config.get_config("request_timeout_seconds")
        )
    except requests.RequestException as exc:
        log(f"Could not add archivepassword '{password}': {exc}", PREFIX, "error")
        return False
    return res.status_code == 200


def jdown_premium_account_is_set(hoster: str, username: str) -> bool:
    query = {
        "username": True,
        "enabled": True,
        "valid": True,
        "trafficLeft": False,
        "trafficMax": False,
    }
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/accounts/queryAccounts",
            params={"": json.dumps(query)},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not query premium accounts: {exc}", PREFIX, "error")
        return False

    accounts = response_data(res, "accounts/queryAccounts", [])
    if not isinstance(accounts, list):
        return False

    for account in accounts:
        if not isinstance(account, dict):
            continue
        account_hoster = account.get("hostname")
        account_username = (account.get("infoMap") or {}).get("username")
        if account_hoster == hoster and account_username == username:
            return True
    return False


def jdown_premium_account_set(hoster: str, username: str, password: str) -> bool:
    log(f"Adding premium account for hoster='{hoster}' user='{username}'", PREFIX, "debug")
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/accounts/addAccount",
            params=[
                ("", hoster),
                ("", username),
                ("", password),
            ],
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not set premium account '{username}@{hoster}': {exc}", PREFIX, "error")
        return False
    return bool(response_data(res, "accounts/addAccount", False))


def jdown_ensure_premium_account() -> bool:
    log("Ensuring premium account is configured", PREFIX, "debug")
    if not config.get_config("premium_account_hoster") or not config.get_config("premium_account_username") or not config.get_config("premium_account_password"):
        log("PREMIUM_ACCOUNT env vars not set, skipping", PREFIX, "debug")
        return True

    if jdown_premium_account_is_set(config.get_config("premium_account_hoster"), config.get_config("premium_account_username")):
        log(f"Premium account '{config.get_config("premium_account_username")}' for '{config.get_config("premium_account_hoster")}' already configured", PREFIX)
        return True

    log(f"Configuring premium account '{config.get_config("premium_account_username")}' for '{config.get_config("premium_account_hoster")}'", PREFIX)
    if not jdown_premium_account_set(config.get_config("premium_account_hoster"), config.get_config("premium_account_username"), config.get_config("premium_account_password")):
        log("Failed to configure premium account", PREFIX, "error")
        return False
    return True

def jdown_downloads_get_status() -> list[dict]:
    """Return all download packages with their state and progress percentage.

    Each entry contains:
        uuid, name, status, running, finished, percent,
        bytes_loaded, bytes_total, speed_bps, eta_seconds, save_to
    """
    ctx = "downloadsV2/queryPackages"
    try:
        res = requests.post(
            f"{config.get_config('api_base_url')}/{ctx}",
            params={"": json.dumps(_DOWNLOAD_STATUS_QUERY)},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not query download status: {exc}", PREFIX, "error")
        return []

    packages = response_data(res, ctx, [])
    if not isinstance(packages, list):
        return []

    result = []
    for pkg in packages:
        bytes_loaded = pkg.get("bytesLoaded") or 0
        bytes_total  = pkg.get("bytesTotal")  or 0
        percent = round(bytes_loaded / bytes_total * 100, 1) if bytes_total > 0 else 0.0
        result.append({
            "uuid":        pkg.get("uuid"),
            "name":        pkg.get("name"),
            "status":      pkg.get("status"),
            "running":     pkg.get("running", False),
            "finished":    pkg.get("finished", False),
            "percent":     percent,
            "bytes_loaded": bytes_loaded,
            "bytes_total":  bytes_total,
            "speed_bps":   pkg.get("speed") or 0,
            "eta_seconds": pkg.get("eta") or -1,
            "save_to":     pkg.get("saveTo"),
        })
    return result


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


def jdown_downloads_start() -> bool:
    ctx = "downloadcontroller/start"
    try:
        res = requests.post(
            f"{config.get_config('api_base_url')}/{ctx}",
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not start download controller: {exc}", PREFIX, "error")
        return False
    result = response_data(res, ctx, False)
    log("Download controller started", PREFIX)
    return bool(result)


def jdown_downloads_stop() -> bool:
    ctx = "downloadcontroller/stop"
    try:
        res = requests.post(
            f"{config.get_config('api_base_url')}/{ctx}",
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not stop download controller: {exc}", PREFIX, "error")
        return False
    result = response_data(res, ctx, False)
    log("Download controller stopped", PREFIX)
    return bool(result)


def jdown_package_set_enabled(package_uuid: int, enabled: bool) -> bool:
    ctx = "downloadsV2/setEnabled"
    try:
        res = requests.post(
            f"{config.get_config('api_base_url')}/{ctx}",
            params=[
                ("", json.dumps(enabled)),
                ("", json.dumps([])),
                ("", json.dumps([package_uuid])),
            ],
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not set enabled={enabled} for package {package_uuid}: {exc}", PREFIX, "error")
        return False
    return res.status_code == 200


def jdown_package_stop(package_uuid: int) -> bool:
    """Abort the active download for a package without leaving it disabled."""
    log(f"Stopping package {package_uuid}", PREFIX, "debug")
    jdown_package_set_enabled(package_uuid, False)
    jdown_package_set_enabled(package_uuid, True)
    return True


def jdown_package_is_finished(package_uuid: int, status: str = None) -> bool:
    """Return True if the package and all its links are finished.

    Uses the same status-string checks as the download watcher:
    a status of 'Finished' or one starting with 'Extraction OK' counts as done.
    """
    def _status_ok(s: str) -> bool:
        return bool(s) and (s == "Finished" or s.startswith("Extraction OK"))

    if not _status_ok(status):
        return False
    links = jdown_downloads_get_package_links([package_uuid])
    if not links:
        return False
    return all(_status_ok(link.get("status") or "") for link in links)


def jdown_package_force_start(package_uuid: int) -> bool:
    log(f"Force starting package {package_uuid}", PREFIX, "debug")
    jdown_package_set_enabled(package_uuid, True)
    ctx = "downloadsV2/forceDownload"
    try:
        res = requests.post(
            f"{config.get_config('api_base_url')}/{ctx}",
            params={
                "linkIds":    json.dumps([]),
                "packageIds": json.dumps([package_uuid]),
            },
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not force start package {package_uuid}: {exc}", PREFIX, "error")
        return False
    return bool(response_data(res, ctx, False))


def jdown_package_remove(package_uuid: int) -> bool:
    log(f"Removing package {package_uuid}", PREFIX, "debug")
    ctx = "downloadsV2/removeLinks"
    try:
        res = requests.post(
            f"{config.get_config('api_base_url')}/{ctx}",
            params={
                "linkIds":    json.dumps([]),
                "packageIds": json.dumps([package_uuid]),
            },
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not remove package {package_uuid}: {exc}", PREFIX, "error")
        return False
    return res.status_code == 200


def jdown_downloads_get_packages(name: str = None):
    ctx = "downloadsV2/queryPackages"
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/{ctx}",
            params={"": json.dumps(_PACKAGES_QUERY)},
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


def jdown_linkgrabber_get_packages(name: str = None):
    ctx = "linkgrabberv2/queryPackages"
    try:
        res = requests.post(
            f"{config.get_config("api_base_url")}/{ctx}",
            params={"": json.dumps(_PACKAGES_QUERY)},
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not query linkgrabber packages: {exc}", PREFIX, "error")
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
            f"{config.get_config("api_base_url")}/{ctx}",
            params={
                "linkIds":    json.dumps([]),
                "packageIds": json.dumps([package_uuid]),
            },
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"Could not move package {package_uuid} to download list: {exc}", PREFIX, "error")
        return False
    return response_data(res, ctx, False) == ""

