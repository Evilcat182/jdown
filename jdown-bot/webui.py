from flask import Flask, jsonify, render_template
import state
from functions import log

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "linkgrabber":    state.linkgrabber_enabled.is_set(),
        "downloads":      state.downloads_enabled.is_set(),
        "plex":           state.plex_scan_enabled.is_set(),
        "delete_source":  state.delete_source_enabled.is_set(),
        "dialogs":        state.dialogs_enabled.is_set(),
    })


@app.route("/api/toggle/<watcher>", methods=["POST"])
def api_toggle(watcher: str):
    if watcher == "linkgrabber":
        ev = state.linkgrabber_enabled
    elif watcher == "downloads":
        ev = state.downloads_enabled
    elif watcher == "plex":
        ev = state.plex_scan_enabled
    elif watcher == "delete_source":
        ev = state.delete_source_enabled
    elif watcher == "dialogs":
        ev = state.dialogs_enabled
    else:
        return jsonify({"error": "unknown watcher"}), 404

    if ev.is_set():
        ev.clear()
        log(f"{watcher} disabled", "[WebUI]")
    else:
        ev.set()
        log(f"{watcher} enabled", "[WebUI]")

    return jsonify({
        "linkgrabber":    state.linkgrabber_enabled.is_set(),
        "downloads":      state.downloads_enabled.is_set(),
        "plex":           state.plex_scan_enabled.is_set(),
        "delete_source":  state.delete_source_enabled.is_set(),
        "dialogs":        state.dialogs_enabled.is_set(),
    })
