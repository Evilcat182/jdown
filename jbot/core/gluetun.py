import json
import requests
import config
from pathlib import Path
from .logger import log

PREFIX = "[Gluetun]"

# servers.json is several MB, so parse it only when it changed
_locations_cache: dict = {"key": None, "data": None}


def gluetun_is_configured() -> bool:
    return bool(config.get_config("gluetun_api_key"))


def _request(method: str, path: str, body: dict = None) -> requests.Response | None:
    try:
        return requests.request(
            method,
            f"{config.get_config('gluetun_api_url')}{path}",
            headers={"X-API-Key": config.get_config("gluetun_api_key")},
            json=body,
            timeout=config.get_config("request_timeout_seconds"),
        )
    except requests.RequestException as exc:
        log(f"{method} {path} failed: {exc}", PREFIX, "debug")
        return None


def _get_json(path: str) -> dict | None:
    res = _request("GET", path)
    if res is None:
        return None
    if res.status_code != 200:
        log(f"GET {path} returned HTTP {res.status_code}: {res.text.strip()}", PREFIX, "debug")
        return None
    try:
        return res.json()
    except ValueError:
        log(f"GET {path} returned invalid JSON: {res.text}", PREFIX, "debug")
        return None


def gluetun_get_settings() -> dict | None:
    """Return the active VPN settings (type, provider, server_selection, ...)."""
    return _get_json("/v1/vpn/settings")


def gluetun_get_status() -> str | None:
    data = _get_json("/v1/vpn/status")
    return data.get("status") if data else None


def gluetun_get_public_ip() -> dict | None:
    return _get_json("/v1/publicip/ip")


def gluetun_get_server_selection() -> dict | None:
    """Return {"countries": [...], "cities": [...]} of the active server filter."""
    settings = gluetun_get_settings()
    if not settings:
        return None
    selection = (settings.get("provider") or {}).get("server_selection") or {}
    return {
        "countries": selection.get("countries") or [],
        "cities":    selection.get("cities") or [],
    }


def gluetun_set_server_selection(country: str, city: str = "") -> tuple[bool, str]:
    """Switch the VPN to another country/city. Gluetun reconnects in place,
    so containers sharing its network keep running. Returns (ok, message)."""
    body = {"provider": {"server_selection": {
        "countries": [country],
        # An empty list clears a previously set city filter
        "cities":    [city] if city else [],
    }}}
    res = _request("PUT", "/v1/vpn/settings", body)
    if res is None:
        return False, "Gluetun control server not reachable"
    message = res.text.strip()
    if res.status_code != 200:
        log(f"Changing VPN server failed: HTTP {res.status_code}: {message}", PREFIX, "error")
        return False, message or f"HTTP {res.status_code}"
    return True, message


def gluetun_get_locations(provider: str, vpn_type: str) -> dict[str, list[str]] | None:
    """Return {country: [cities]} for a provider from gluetun's servers.json,
    or None if the file is not available."""
    path = Path(config.get_config("gluetun_servers_file"))
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None

    cache_key = (str(path), mtime, provider, vpn_type)
    if _locations_cache["key"] == cache_key:
        return _locations_cache["data"]

    try:
        servers = json.loads(path.read_text()).get(provider, {}).get("servers", [])
    except (OSError, ValueError) as exc:
        log(f"Could not read '{path}': {exc}", PREFIX, "error")
        return None

    locations: dict[str, set[str]] = {}
    for server in servers:
        if vpn_type and server.get("vpn") != vpn_type:
            continue
        country = server.get("country")
        if not country:
            continue
        cities = locations.setdefault(country, set())
        if server.get("city"):
            cities.add(server["city"])

    data = {country: sorted(cities) for country, cities in sorted(locations.items())}
    _locations_cache.update(key=cache_key, data=data)
    return data
