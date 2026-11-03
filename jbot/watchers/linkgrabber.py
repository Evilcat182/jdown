import time
import threading
from core import log, jdown_wait_ready, jdown_linkgrabber_get_packages, jdown_download_package

PREFIX = "[AutoDownload]"
SETTLE_SECONDS = 4

# Pseudo-hosts JDownloader uses for placeholder links (e.g. a crawler blocked by Cloudflare)
_DUMMY_HOSTS = {"linkcrawlerretry"}


def _skip_reason(pkg: dict) -> str | None:
    """Return why a package must not be auto-started, or None if it is fine."""
    hosts = {h.lower() for h in (pkg.get("hosts") or [])}
    if hosts & _DUMMY_HOSTS:
        return "placeholder link (crawler could not resolve it)"
    if pkg.get("availableOfflineCount", 0) > 0:
        return f"{pkg['availableOfflineCount']} link(s) offline"
    return None


def _check_packages(seen_uuids: set[int], pkg_state: dict[int, list]):
    packages = jdown_linkgrabber_get_packages()
    now = time.time()
    for pkg in packages:
        uid = pkg.get("uuid")
        name = pkg.get("name", "?")
        total = pkg.get("bytesTotal", 0)

        if uid not in seen_uuids:
            seen_uuids.add(uid)
            pkg_state[uid] = [total, now, False]
            log(f"New package found: {name}", PREFIX)
            continue

        last_total, last_changed, ready = pkg_state[uid]
        if total != last_total:
            pkg_state[uid] = [total, now, False]
        elif not ready and (now - last_changed) >= SETTLE_SECONDS:
            pkg_state[uid][2] = True
            reason = _skip_reason(pkg)
            if reason:
                log(f"Not starting '{name}': {reason}", PREFIX, "warning")
                continue
            log(f"Package ready: {name} ({total} bytes)", PREFIX)
            ok = jdown_download_package(uid)
            if ok:
                log(f"Download started: {name}", PREFIX)
            else:
                log(f"Failed to start: {name}", PREFIX, "warning")


def run(enabled: threading.Event):
    log("Starting linkgrabber watcher", PREFIX)
    seen_uuids: set[int] = set()
    # uid -> [last_bytesTotal, last_changed_time, ready_reported]
    pkg_state: dict[int, list] = {}

    while True:
        if not enabled.is_set():
            time.sleep(1)
            continue
        try:
            jdown_wait_ready()
            _check_packages(seen_uuids, pkg_state)
        except Exception as exc:
            log(f"Unexpected error: {exc}", PREFIX, "error")
        time.sleep(2)
