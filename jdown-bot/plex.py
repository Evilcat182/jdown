import requests, os

PREFIX = "[PLEX-API]"
PLEX_TOKEN = os.getenv("PLEX_TOKEN","")
PLEX_API_ROOT = os.getenv("PLEX_API_ROOT","")
REQUEST_TIMEOUT_SECONDS = 10
PLEX_MOVIE_LIB_NAME = os.getenv("PLEX_MOVIE_LIB_NAME","")
PLEX_SHOW_LIB_NAME = os.getenv("PLEX_SHOW_LIB_NAME","")

def plex_check():
    return bool(PLEX_TOKEN and PLEX_API_ROOT)

def plex_library_get_all():
    HEADERS = {
        "X-Plex-Token": PLEX_TOKEN,
        "Accept": "application/json",
    }
    try:
        res = requests.get(
            f"{PLEX_API_ROOT}/library/sections",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"{PREFIX} Error: Could not connect to Plex at {PLEX_API_ROOT}. Check IP/port.")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"{PREFIX} Error: Plex returned HTTP {e.response.status_code} when fetching libraries.")
        return []
    except requests.exceptions.Timeout:
        print(f"{PREFIX} Error: Request to Plex timed out after {REQUEST_TIMEOUT_SECONDS}s.")
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
        print(f"{PREFIX} Error: No {lib_type} library found matching: {names}")
        return None
    return matches[0]

def plex_scan_library(lib_type: str):
    if not plex_check():
        print(f"{PREFIX} WARNING: PLEX_TOKEN or PLEX_API_ROOT env var not set ... Skipping Plex scan")
        return

    HEADERS = {
        "X-Plex-Token": PLEX_TOKEN,
        "Accept": "application/json",
    }
    library_names = {
        "movie": [PLEX_MOVIE_LIB_NAME] if PLEX_MOVIE_LIB_NAME else None,
        "show": [PLEX_SHOW_LIB_NAME] if PLEX_SHOW_LIB_NAME else None,
    }
    section_id = plex_library_get_id(lib_type, library_names[lib_type])
    if section_id is None:
        print(f"{PREFIX} No {lib_type} library found.")
        return
    try:
        res = requests.get(
            f"{PLEX_API_ROOT}/library/sections/{section_id}/refresh",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"{PREFIX} Error: Could not connect to Plex at {PLEX_API_ROOT}. Check IP/port.")
        return
    except requests.exceptions.HTTPError as e:
        print(f"{PREFIX} Error: Plex returned HTTP {e.response.status_code} when triggering scan.")
        return
    except requests.exceptions.Timeout:
        print(f"{PREFIX} Error: Scan request timed out after {REQUEST_TIMEOUT_SECONDS}s.")
        return
    print(f"{PREFIX} Scan triggered for {lib_type} library (section {section_id}).")
