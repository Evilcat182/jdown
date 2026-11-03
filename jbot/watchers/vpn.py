import time
import config
from core import (
    log, gluetun_is_configured, gluetun_get_server_selection, gluetun_set_server_selection,
    gluetun_get_status, gluetun_get_connection, gluetun_restart_vpn,
)
from core.gluetun import switch_lock

PREFIX = "[VPN]"
POLL_INTERVAL = 30   # seconds between checks
STUCK_AFTER = 120    # reconnect if gluetun has no tunnel for this long


def _matches(current: list[str], wanted: list[str]) -> bool:
    return sorted(v.casefold() for v in current) == sorted(v.casefold() for v in wanted)


def enforce_selection(last_error: str | None = None) -> str | None:
    """Re-apply the saved VPN server choice if gluetun runs with something else
    (e.g. its compose default after a container restart).
    Returns the current error message, so repeated failures are logged once."""
    country = config.get_config("vpn_country")
    city = config.get_config("vpn_city")
    if not country:
        return None

    current = gluetun_get_server_selection()
    if current is None:
        return last_error  # gluetun not reachable (yet), try again next round

    if _matches(current["countries"], [country]) and _matches(current["cities"], [city] if city else []):
        return None

    target = f"{country}/{city}" if city else country
    ok, message = gluetun_set_server_selection(country, city)
    if ok:
        log(f"Re-applied saved VPN server '{target}'", PREFIX)
        return None
    error = f"Could not apply saved VPN server '{target}': {message}"
    if error != last_error:
        log(error, PREFIX, "error")
    return error


def check_tunnel(down_since: float | None) -> float | None:
    """Reconnect when gluetun has been without a tunnel for STUCK_AFTER seconds.
    OpenVPN keeps retrying a dead or rejecting server (TLS timeout, AUTH_FAILED)
    forever, a reconnect makes gluetun pick another server from the filter.
    Returns the time the tunnel went down, or None while it is up."""
    if gluetun_get_status() != "running":
        return None  # stopped on purpose or not reachable, nothing to repair
    if gluetun_get_connection():
        if down_since is not None:
            log("VPN connection is back", PREFIX)
        return None

    now = time.monotonic()
    if down_since is None:
        return now
    if now - down_since < STUCK_AFTER:
        return down_since
    log(f"No VPN connection for {int(now - down_since)}s, reconnecting to another server", PREFIX, "warning")
    gluetun_restart_vpn()
    return now


def run():
    if not gluetun_is_configured():
        log("GLUETUN_API_KEY not set, VPN server selection disabled", PREFIX, "warning")
        return
    log("Starting VPN watcher", PREFIX)
    last_error = None
    down_since = None
    while True:
        try:
            # A switch from the web UI is waiting for its tunnel, leave it alone
            if switch_lock.acquire(blocking=False):
                try:
                    last_error = enforce_selection(last_error)
                    down_since = check_tunnel(down_since)
                finally:
                    switch_lock.release()
            else:
                down_since = None
        except Exception as exc:
            log(f"Unexpected error: {exc}", PREFIX, "error")
        time.sleep(POLL_INTERVAL)
