import requests
import config
from core import log

PREFIX = "[PLEX-API]"


def plex_check():
    return bool(config.get_config("plex_token") and config.get_config("plex_api_root"))


def plex_library_get_all():
    headers = {
        "X-Plex-Token": config.get_config("plex_token"),
        "Accept": "application/json",
    }
    try:
        res = requests.get(
            f"{config.get_config("plex_api_root")}/library/sections",
            headers=headers,
            timeout=config.get_config("request_timeout_seconds"),
        )
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        log(f"Could not connect to Plex at {config.get_config("plex_api_root")}. Check IP/port.", PREFIX, "error")
        return []
    except requests.exceptions.HTTPError as e:
        log(f"Plex returned HTTP {e.response.status_code} when fetching libraries.", PREFIX, "error")
        return []
    except requests.exceptions.Timeout:
        log(f"Request to Plex timed out after {config.get_config("request_timeout_seconds")}s.", PREFIX, "error")
        return []
    return res.json()["MediaContainer"]["Directory"]


def plex_library_get_id(lib_type: str, library_names: list[str] = None):
    guess_names = {
        "movie": ["filme", "movies"],
        "show": ["serien", "series"],
    }
    libraries = plex_library_get_all()
    filtered = [lib for lib in libraries if lib["type"] == lib_type]
    names = [n.casefold() for n in (library_names or []) if n]
    if not names:
        names = guess_names[lib_type]
    matches = [lib["key"] for lib in filtered if lib["title"].casefold() in names]
    if not matches:
        log(f"No {lib_type} library found matching: {names}", PREFIX, "error")
        return None
    return matches[0]


def plex_scan_library(lib_type: str):
    if not plex_check():
        log("PLEX_TOKEN or PLEX_API_ROOT env var not set ... Skipping Plex scan", PREFIX, "warning")
        return

    headers = {
        "X-Plex-Token": config.get_config("plex_token"),
        "Accept": "application/json",
    }
    library_names = {
        "movie": [config.get_config("plex_movie_lib_name")] if config.get_config("plex_movie_lib_name") else None,
        "show":  [config.get_config("plex_show_lib_name")]  if config.get_config("plex_show_lib_name")  else None,
    }
    section_id = plex_library_get_id(lib_type, library_names[lib_type])
    if section_id is None:
        log(f"No {lib_type} library found.", PREFIX, "error")
        return
    try:
        res = requests.get(
            f"{config.get_config("plex_api_root")}/library/sections/{section_id}/refresh",
            headers=headers,
            timeout=config.get_config("request_timeout_seconds"),
        )
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        log(f"Could not connect to Plex at {config.get_config("plex_api_root")}. Check IP/port.", PREFIX, "error")
        return
    except requests.exceptions.HTTPError as e:
        log(f"Plex returned HTTP {e.response.status_code} when triggering scan.", PREFIX, "error")
        return
    except requests.exceptions.Timeout:
        log(f"Scan request timed out after {config.get_config("request_timeout_seconds")}s.", PREFIX, "error")
        return
    log(f"Scan triggered for {lib_type} library (section {section_id}).", PREFIX)
