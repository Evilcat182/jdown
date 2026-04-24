import requests
import time
from settings import DEBUG, API_BASE_URL, REQUEST_TIMEOUT_SECONDS, WAIT_TIMEOUT_SECONDS, COLOR_RESET, COLOR_GREY, COLOR_RED, COLOR_YELLOW, COLOR_GREEN

def log(message: str, prefix: str = "", type: str = None):
    p = f"{prefix} " if prefix else ""
    if type == "debug":
        if DEBUG:
            print(f"{COLOR_GREY}{p}{message}{COLOR_RESET}")
    elif type == "warning":
        print(f"{COLOR_YELLOW}{p}{message}{COLOR_RESET}")
    elif type == "error":
        print(f"{COLOR_RED}{p}ERROR: {message}{COLOR_RESET}")
    elif type == "success":
        print(f"{COLOR_GREEN}{p}{message}{COLOR_RESET}")
    else:
        print(f"{p}{message}")

def response_data(res: requests.Response, context: str, default):
    if res.status_code != 200:
        log(f"{context} returned HTTP {res.status_code}: {res.text}", type="debug")
        return default
    try:
        body = res.json()
    except ValueError:
        log(f"{context} returned invalid JSON: {res.text}", type="debug")
        return default
    if "data" not in body:
        log(f"{context} response has no 'data' key: {body}", type="debug")
        return default
    return body["data"]

def jdown_is_ready() -> bool:

    try:
        res = requests.get(f"{API_BASE_URL}/jd/version", timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        log(f"Could not reach JDownloader API: {exc}", type="debug")
        return False
    return res.status_code == 200

def jdown_wait_ready(timeout_seconds: int = WAIT_TIMEOUT_SECONDS) -> bool:
    start = time.time()
    while not jdown_is_ready():
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for JDownloader to become ready", type="error")
            return False
        time.sleep(1)
    return True

def jdown_wait_not_ready(timeout_seconds: int = WAIT_TIMEOUT_SECONDS) -> bool:
    start = time.time()
    while jdown_is_ready():
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for JDownloader to go down", type="error")
            return False
        time.sleep(1)
    return True