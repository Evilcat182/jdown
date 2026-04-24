from settings import DEBUG, COLOR_RESET, COLOR_GREY, COLOR_RED, COLOR_YELLOW, COLOR_GREEN


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
