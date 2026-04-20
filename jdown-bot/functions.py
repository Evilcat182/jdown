import requests
import time
from settings import DEBUG, API_BASE_URL, REQUEST_TIMEOUT_SECONDS, WAIT_TIMEOUT_SECONDS

def debug_log(message: str):
    if DEBUG:
        print(message)

def error_log(message: str):
    print(f"ERROR: {message}")

def response_data(res: requests.Response, context: str, default):
    if res.status_code != 200:
        debug_log(f"{context} returned HTTP {res.status_code}: {res.text}")
        return default
    try:
        body = res.json()
    except ValueError:
        debug_log(f"{context} returned invalid JSON: {res.text}")
        return default
    if "data" not in body:
        debug_log(f"{context} response has no 'data' key: {body}")
        return default
    return body["data"]

def jdown_is_ready() -> bool:

    try:
        res = requests.get(f"{API_BASE_URL}/jd/version", timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        debug_log(f"Could not reach JDownloader API: {exc}")
        return False
    return res.status_code == 200

def jdown_wait_ready(timeout_seconds: int = WAIT_TIMEOUT_SECONDS) -> bool:
    start = time.time()
    while not jdown_is_ready():
        if time.time() - start > timeout_seconds:
            error_log("Timeout while waiting for JDownloader to become ready")
            return False
        time.sleep(1)
    return True

def jdown_wait_not_ready(timeout_seconds: int = WAIT_TIMEOUT_SECONDS) -> bool:
    start = time.time()
    while jdown_is_ready():
        if time.time() - start > timeout_seconds:
            error_log("Timeout while waiting for JDownloader to go down")
            return False
        time.sleep(1)
    return True