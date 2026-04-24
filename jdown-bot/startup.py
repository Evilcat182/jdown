import requests
import time
import sys
import json
from settings import *
from functions import *

def jdown_get_dialog() -> list:
    log("Querying pending dialogs", type="debug")
    try:
        res = requests.post(
            f"{API_BASE_URL}/dialogs/list",
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        log(f"While getting Dialog: {exc}", type="error")
        return []
    data = response_data(res, "dialogs/list", [])
    return data if isinstance(data, list) else []

def jdown_wait_for_dialog(timeout_seconds: int = WAIT_TIMEOUT_SECONDS) -> list:
    log(f"Waiting for install dialog (timeout={timeout_seconds}s)", type="debug")
    start = time.time()
    while True:
        dialogs = jdown_get_dialog()
        if dialogs:
            log(f"Dialog(s) detected: {dialogs}", type="debug")
            return dialogs
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for install dialog", type="error")
            return []
        time.sleep(1)

def jdown_config_set(interface_name: str, storage: str, key: str, value: object) -> bool:
    log(
        f"Setting config interface='{interface_name}' storage='{storage}' key='{key}' value='{value}'",
        type="debug"
    )
    try:
        res = requests.post(
            f"{API_BASE_URL}/config/set",
            params=[
                ("", interface_name),
                ("", storage),
                ("", key),
                ("", value)
            ],
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        log(f"Could not set config '{interface_name}': {exc}", type="error")
        return False
    return bool(response_data(res, "config/set", False))

def jdown_archivepassword_add(password: str) -> bool:
    log(f"Adding archive password (len={len(password)})", type="debug")
    try:
        res = requests.post(
            f"{API_BASE_URL}/extraction/addArchivePassword",
            params={"": password},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        log(f"Could not add archivepassword '{password}': {exc}", type="error")
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
            f"{API_BASE_URL}/accounts/queryAccounts",
            params={"": json.dumps(query)},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        log(f"Could not query premium accounts: {exc}", type="error")
        return False

    accounts = response_data(res, "accounts/queryAccounts", [])
    if not isinstance(accounts, list):
        return False

    for account in accounts:
        if not isinstance(account, dict):
            continue
        account_hoster = account.get("hostname")
        account_username = account.get("infoMap")["username"]
        if account_hoster == hoster and account_username == username:
            return True
    return False

def jdown_premium_account_set(hoster: str, username: str, password: str) -> bool:
    log(f"Adding premium account for hoster='{hoster}' user='{username}'", type="debug")
    try:
        res = requests.post(
            f"{API_BASE_URL}/accounts/addAccount",
            params=[
                ("", hoster),
                ("", username),
                ("", password),
            ],
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        log(f"Could not set premium account '{username}@{hoster}': {exc}", type="error")
        return False
    return bool(response_data(res, "accounts/addAccount", False))

def jdown_ensure_premium_account() -> bool:
    log("Ensuring premium account is configured", type="debug")
    if not PREMIUM_ACCOUNT_HOSTER or not PREMIUM_ACCOUNT_USERNAME or not PREMIUM_ACCOUNT_PASSWORD:
        log("PREMIUM_ACCOUNT env vars not set, skipping", type="debug")
        return True

    if jdown_premium_account_is_set(PREMIUM_ACCOUNT_HOSTER, PREMIUM_ACCOUNT_USERNAME):
        log(f"Premium account '{PREMIUM_ACCOUNT_USERNAME}' for '{PREMIUM_ACCOUNT_HOSTER}' already configured")
        return True

    log(f"Configuring premium account '{PREMIUM_ACCOUNT_USERNAME}' for '{PREMIUM_ACCOUNT_HOSTER}'")
    if not jdown_premium_account_set(PREMIUM_ACCOUNT_HOSTER, PREMIUM_ACCOUNT_USERNAME, PREMIUM_ACCOUNT_PASSWORD):
        log("Failed to configure premium account", type="error")
        return False
    return True


#############################
#############################

log(f"startup.py started with API_BASE_URL='{API_BASE_URL}'", type="debug")
log(f"startup.py DEBUG mode is {'ON' if DEBUG else 'OFF'}", type="debug")
log("Waiting for JDownloader to get ready ...")
if not jdown_wait_ready():
    log("JDownloader did not become ready in time", type="error")
    sys.exit(1)

log("JDownloader is ready", type="debug")
for pwd in EXTRACTION_PASSWORDS.split(","):
    pwd = pwd.strip()
    if not pwd:
        continue
    if jdown_archivepassword_add(pwd):
        log(f"Added Archive extract Password '{pwd}'")
    else:
        log(f"Failed to add Archive extract Password '{pwd}'", type="error"))

if not jdown_ensure_premium_account():
    log("Premium account setup failed, continuing anyway", type="error")

# SET DeleteArchiveFilesAfterExtractionAction to "Delete files from disk"
log("Setting config DeleteArchiveFilesAfterExtractionAction to 'Delete files from disk'")
if not jdown_config_set(
    "org.jdownloader.extensions.extraction.ExtractionConfig",
    "cfg/org.jdownloader.extensions.extraction.ExtractionExtension",
    "DeleteArchiveFilesAfterExtractionAction",
    "NULL"
):
    log("Failed to set DeleteArchiveFilesAfterExtractionAction", type="error")
    sys.exit(1)

# SET IfFileExistsAction to "Auto-Rename the new File"
log("Setting config IfFileExistsAction to 'Auto-Rename the new File'")
if not jdown_config_set(
    "org.jdownloader.extensions.extraction.ExtractionConfig",
    "cfg/org.jdownloader.extensions.extraction.ExtractionExtension",
    "IfFileExistsAction",
    "AUTO_RENAME"
):
    log("Failed to set IfFileExistsAction", type="error")
    sys.exit(1)

log("startup.py finished successfully", type="debug")
