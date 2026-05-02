from .logger import log, get_logs

__all__ = ["log", "get_logs", "response_data", "jdown_is_ready", "jdown_wait_ready", "jdown_wait_not_ready"]


def __getattr__(name):
    if name in {"response_data", "jdown_is_ready", "jdown_wait_ready", "jdown_wait_not_ready"}:
        from . import jdownloader
        return getattr(jdownloader, name)
    raise AttributeError(f"module 'core' has no attribute '{name}'")
