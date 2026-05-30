from .logger import log, get_logs

__all__ = [
    "log",
    "get_logs",
    "response_data",
    "jdown_is_ready",
    "jdown_wait_ready",
    "jdown_wait_not_ready",
    "jdown_wait_for_dialog",
    "jdown_archivepassword_add",
    "jdown_ensure_premium_account",
    "jdown_config_set",
    "jdown_list_dialogs",
    "jdown_get_dialog",
    "jdown_get_dialog_type_info",
    "jdown_answer_dialog",
    "jdown_downloads_get_state",
    "jdown_downloads_start",
    "jdown_downloads_stop",
    "jdown_package_set_enabled",
    "jdown_package_stop",
    "jdown_package_force_start",
    "jdown_package_remove",
    "jdown_downloads_get_status",
    "jdown_downloads_get_packages",
    "jdown_downloads_get_package_links",
    "jdown_get_archive_info",
    "jdown_linkgrabber_get_packages",
    "jdown_download_package",
]

_lazy = [
    "response_data",
    "jdown_is_ready",
    "jdown_wait_ready",
    "jdown_wait_not_ready",
    "jdown_wait_for_dialog",
    "jdown_archivepassword_add",
    "jdown_ensure_premium_account",
    "jdown_config_set",
    "jdown_list_dialogs",
    "jdown_get_dialog",
    "jdown_get_dialog_type_info",
    "jdown_answer_dialog",
    "jdown_downloads_get_state",
    "jdown_downloads_start",
    "jdown_downloads_stop",
    "jdown_package_set_enabled",
    "jdown_package_stop",
    "jdown_package_is_finished",
    "jdown_package_force_start",
    "jdown_package_remove",
    "jdown_downloads_get_status",
    "jdown_downloads_get_packages",
    "jdown_downloads_get_package_links",
    "jdown_get_archive_info",
    "jdown_linkgrabber_get_packages",
    "jdown_download_package",
]


def __getattr__(name):
    if name in _lazy:
        from . import jdownloader
        return getattr(jdownloader, name)
    raise AttributeError(f"module 'core' has no attribute '{name}'")
