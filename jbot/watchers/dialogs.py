import time
import threading
import config

from core import log, jdown_list_dialogs, jdown_get_dialog, jdown_get_dialog_type_info, jdown_answer_dialog

PREFIX = "[DialogHandler]"
POLL_INTERVAL = 2  # seconds between polls

# Configure which dialog types to auto-answer and what data to send.
# Key: dialog type string (as returned by the API)
# Value: dict to send as the answer data map.
# Tip: set DEBUG=1 and check logs — on answer failure the expected
#      "out" schema is printed so you can correct the keys here.
DIALOG_RULES: dict[str, dict] = {
    "org.appwork.uio.ConfirmDialogInterface": {"closereason": "OK", "dontshowagainselected": "false"},
}

def handle_dialogs():
    ids = jdown_list_dialogs()
    for dialog_id in ids:
        info = jdown_get_dialog(dialog_id)
        if not info or "type" not in info:
            continue
        dialog_type = info["type"]
        if dialog_type in DIALOG_RULES:
            answer_data = DIALOG_RULES[dialog_type]
            log(f"Auto-answering dialog {dialog_id} (type={dialog_type})", PREFIX, "debug")
            jdown_answer_dialog(dialog_id, answer_data, dialog_type)
        else:
            log(f"No rule for dialog type '{dialog_type}', skipping", PREFIX, "debug")


def run(enabled: threading.Event = None):
    log(f"Starting dialog watcher (rules: {list(DIALOG_RULES.keys())})", PREFIX)
    while True:
        if enabled is not None and not enabled.is_set():
            time.sleep(1)
            continue
        try:
            handle_dialogs()
        except Exception as exc:
            log(f"Unexpected error: {exc}", PREFIX, "error")
        time.sleep(POLL_INTERVAL)
