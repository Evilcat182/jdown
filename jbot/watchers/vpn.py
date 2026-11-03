import time
import config
from core import log, gluetun_is_configured, gluetun_get_server_selection, gluetun_set_server_selection

PREFIX = "[VPN]"
POLL_INTERVAL = 30  # seconds between checks


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


def run():
    if not gluetun_is_configured():
        log("GLUETUN_API_KEY not set, VPN server selection disabled", PREFIX, "warning")
        return
    log("Starting VPN watcher", PREFIX)
    last_error = None
    while True:
        try:
            last_error = enforce_selection(last_error)
        except Exception as exc:
            log(f"Unexpected error: {exc}", PREFIX, "error")
        time.sleep(POLL_INTERVAL)
