from flask import Flask, jsonify, render_template
import state
from core import log

app = Flask(__name__)

PREFIX = "[WebUI]"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "linkgrabber":   state.linkgrabber_enabled.is_set(),
        "downloads":     state.downloads_enabled.is_set(),
        "plex":          state.plex_scan_enabled.is_set(),
        "delete_source": state.delete_source_enabled.is_set(),
        "dialogs":       state.dialogs_enabled.is_set(),
    })


@app.route("/api/toggle/<watcher>", methods=["POST"])
def api_toggle(watcher: str):
    mapping = {
        "linkgrabber":   state.linkgrabber_enabled,
        "downloads":     state.downloads_enabled,
        "plex":          state.plex_scan_enabled,
        "delete_source": state.delete_source_enabled,
        "dialogs":       state.dialogs_enabled,
    }
    ev = mapping.get(watcher)
    if ev is None:
        return jsonify({"error": "unknown watcher"}), 404

    if ev.is_set():
        ev.clear()
        log(f"{watcher} disabled", PREFIX)
    else:
        ev.set()
        log(f"{watcher} enabled", PREFIX)

    return jsonify({
        "linkgrabber":   state.linkgrabber_enabled.is_set(),
        "downloads":     state.downloads_enabled.is_set(),
        "plex":          state.plex_scan_enabled.is_set(),
        "delete_source": state.delete_source_enabled.is_set(),
        "dialogs":       state.dialogs_enabled.is_set(),
    })
