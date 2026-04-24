import threading
import os

linkgrabber_enabled = threading.Event()
downloads_enabled = threading.Event()
plex_scan_enabled = threading.Event()
delete_source_enabled = threading.Event()
dialogs_enabled = threading.Event()

if os.getenv("AUTOSTART_DOWNLOADS", "1") == "1":
    linkgrabber_enabled.set()

if os.getenv("AUTOORGANIZE_DOWNLOADS", "1") == "1":
    downloads_enabled.set()

if os.getenv("PLEX_SCAN_ENABLED", "1") == "1":
    plex_scan_enabled.set()

if os.getenv("DELETE_SOURCE", "1") == "1":
    delete_source_enabled.set()

if os.getenv("AUTOANSWER_DIALOGS", "1") == "1":
    dialogs_enabled.set()
