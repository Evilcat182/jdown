import config
from .gluetun import (
    gluetun_set_server_selection, gluetun_wait_connected, gluetun_restart_vpn,
    CONNECT_TIMEOUT, CONNECT_ATTEMPTS,
)
from .jdownloader import jdown_downloads_suspend, jdown_downloads_resume
from .logger import log

PREFIX = "[VPN]"


def _label(country: str, city: str) -> str:
    return f"{country}/{city}" if city else country


def wait_for_tunnel(target: str) -> dict | None:
    """Wait for a tunnel, reconnecting between attempts. OpenVPN retries a dead
    or rejecting server forever, a reconnect makes gluetun pick another one."""
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        info = gluetun_wait_connected(CONNECT_TIMEOUT)
        if info or attempt == CONNECT_ATTEMPTS:
            return info
        log(f"No VPN connection to '{target}' within {CONNECT_TIMEOUT}s, trying another server", PREFIX)
        gluetun_restart_vpn()
    return None


def remember_downloads(state: str | None):
    """Keep a stopped downloads state until the VPN watcher sees a tunnel again."""
    if state:
        config.patch_config({"vpn_resume_downloads": state})
        log("Downloads stay stopped until the VPN is connected", PREFIX, "warning")


def switch_server(country: str, city: str = "", fallback: tuple[str, str] | None = None,
                  resume: str | None = None) -> dict:
    """Switch gluetun to another server with downloads stopped in between,
    because running downloads lose their connections when the tunnel drops.

    resume:   downloads state to set once connected, default is the state
              found before the switch.
    fallback: (country, city) to go back to if no server connects.

    Returns {"ok", "status", "message"/"error", "public_ip", "downloads"}.
    The caller must hold gluetun.switch_lock."""
    target = _label(country, city)
    before = jdown_downloads_suspend()
    downloads = resume or before

    ok, message = gluetun_set_server_selection(country, city)
    if not ok:
        jdown_downloads_resume(downloads)
        return {"ok": False, "status": 502, "error": message}

    info = wait_for_tunnel(target)
    if info:
        # Persist only once it works, the VPN watcher re-applies it after restarts
        config.patch_config({"vpn_country": country, "vpn_city": city})
        log(f"VPN server changed to '{target}' (IP {info.get('public_ip')})", PREFIX)
        jdown_downloads_resume(downloads)
        return {"ok": True, "status": 200, "message": message, "public_ip": info, "downloads": downloads}

    error = f"No VPN connection to '{target}' after trying {CONNECT_ATTEMPTS} servers"
    if fallback and fallback[0]:
        back = _label(*fallback)
        log(f"{error}, switching back to '{back}'", PREFIX, "warning")
        gluetun_set_server_selection(*fallback)
        error += f", switched back to '{back}'"
        # Only restart downloads once the previous server is connected again
        if downloads and gluetun_wait_connected(CONNECT_TIMEOUT):
            jdown_downloads_resume(downloads)
            downloads = None
    else:
        log(error, PREFIX, "warning")
    if downloads:
        remember_downloads(downloads)
        error += ". Downloads restart once the VPN is connected"
    return {"ok": False, "status": 504, "error": error + ". Check the gluetun logs."}
