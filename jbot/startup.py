import sys
import config
from core import log, jdown_wait_ready, jdown_archivepassword_add, jdown_ensure_premium_account, jdown_config_set

log(f"startup.py started with API_BASE_URL='{config.get_config("api_base_url")}'", type="debug")
log(f"startup.py DEBUG mode is {'ON' if config.get_config("debug") else 'OFF'}", type="debug")
log("Waiting for JDownloader to get ready ...")
if not jdown_wait_ready():
    log("JDownloader did not become ready in time", type="error")
    sys.exit(1)

log("JDownloader is ready", type="debug")
for pwd in config.get_config("extraction_passwords").split(","):
    pwd = pwd.strip()
    if not pwd:
        continue
    if jdown_archivepassword_add(pwd):
        log(f"Added Archive extract Password '{pwd}'")
    else:
        log(f"Failed to add Archive extract Password '{pwd}'", type="error")

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
