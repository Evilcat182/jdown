import requests
import time
import config
from .logger import log

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
        res = requests.get(f"{config.get_config("api_base_url")}/jd/version", timeout=config.get_config("request_timeout_seconds"))
    except requests.RequestException as exc:
        log(f"Could not reach JDownloader API: {exc}", type="debug")
        return False
    return res.status_code == 200


def jdown_wait_ready(timeout_seconds: int = config.get_config("wait_timeout_seconds")) -> bool:
    start = time.time()
    while not jdown_is_ready():
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for JDownloader to become ready", type="error")
            return False
        time.sleep(1)
    return True


def jdown_wait_not_ready(timeout_seconds: int = config.get_config("wait_timeout_seconds")) -> bool:
    start = time.time()
    while jdown_is_ready():
        if time.time() - start > timeout_seconds:
            log("Timeout while waiting for JDownloader to go down", type="error")
            return False
        time.sleep(1)
    return True
