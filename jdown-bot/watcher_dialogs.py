import time
import threading
import requests
import json
from settings import API_BASE_URL, REQUEST_TIMEOUT_SECONDS
from functions import debug_log, error_log, response_data

PREFIX = "[DialogHandler]"

# Configure which dialog types to auto-answer and what data to send.
# Key: dialog type string (as returned by the API)
# Value: dict to send as the answer data map.
# Tip: set DEBUG=1 and check logs — on answer failure the expected
#      "out" schema is printed so you can correct the keys here.
DIALOG_RULES: dict[str, dict] = {
    "org.appwork.uio.ConfirmDialogInterface": {"closereason": "OK", "dontshowagainselected": "false"},
}

POLL_INTERVAL = 2  # seconds between polls


def jdown_list_dialogs() -> list[int]:
    debug_log(f"{PREFIX} Listing pending dialogs")
    try:
        res = requests.post(
            f"{API_BASE_URL}/dialogs/list",
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        error_log(f"{PREFIX} While listing dialogs: {exc}")
        return []
    data = response_data(res, "dialogs/list", [])
    return data if isinstance(data, list) else []


def jdown_get_dialog(dialog_id: int) -> dict | None:
    debug_log(f"{PREFIX} Getting dialog info for id={dialog_id}")
    try:
        res = requests.post(
            f"{API_BASE_URL}/dialogs/get",
            params={"id": dialog_id, "icon": "false", "properties": "true"},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        error_log(f"{PREFIX} While getting dialog {dialog_id}: {exc}")
        return None
    return response_data(res, "dialogs/get", None)


def jdown_get_dialog_type_info(dialog_type: str) -> dict | None:
    debug_log(f"{PREFIX} Fetching type info for '{dialog_type}'")
    try:
        res = requests.post(
            f"{API_BASE_URL}/dialogs/getTypeInfo",
            params={"dialogType": dialog_type},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        error_log(f"{PREFIX} While getting type info: {exc}")
        return None
    return response_data(res, "dialogs/getTypeInfo", None)


def jdown_answer_dialog(dialog_id: int, data: dict, dialog_type: str = "") -> bool:
    debug_log(f"{PREFIX} Answering dialog id={dialog_id} with {data}")
    try:
        res = requests.post(
            f"{API_BASE_URL}/dialogs/answer",
            params={"id": dialog_id, "data": json.dumps(data)},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        error_log(f"{PREFIX} While answering dialog {dialog_id}: {exc}")
        return False
    if res.status_code != 200:
        error_log(f"{PREFIX} Answer dialog {dialog_id} failed: {res.status_code} {res.text}")
        if dialog_type:
            type_info = jdown_get_dialog_type_info(dialog_type)
            if type_info:
                error_log(f"{PREFIX} Expected answer schema (in) for '{dialog_type}': {type_info.get('in')}")
                error_log(f"{PREFIX} Dialog output schema (out) for '{dialog_type}': {type_info.get('out')}")
        return False
    print(f"{PREFIX} Dialog {dialog_id} answered and closed (type={dialog_type})")
    return True


def handle_dialogs():
    ids = jdown_list_dialogs()
    for dialog_id in ids:
        info = jdown_get_dialog(dialog_id)
        if not info or "type" not in info:
            continue
        dialog_type = info["type"]
        if dialog_type in DIALOG_RULES:
            answer_data = DIALOG_RULES[dialog_type]
            debug_log(f"{PREFIX} Auto-answering dialog {dialog_id} (type={dialog_type})")
            jdown_answer_dialog(dialog_id, answer_data, dialog_type)
        else:
            debug_log(f"{PREFIX} No rule for dialog type '{dialog_type}', skipping")


def run(enabled: threading.Event = None):
    print(f"{PREFIX} Starting dialog watcher (rules: {list(DIALOG_RULES.keys())})")
    while True:
        if enabled is not None and not enabled.is_set():
            time.sleep(1)
            continue
        try:
            handle_dialogs()
        except Exception as exc:
            error_log(f"{PREFIX} Unexpected error: {exc}")
        time.sleep(POLL_INTERVAL)
