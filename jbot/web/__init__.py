import os
import sys
import threading
from pathlib import Path
from flask import Flask, jsonify, render_template, request
import state
from core import log, get_logs
from media.organizer import organize

app = Flask(__name__)

PREFIX = "[WebUI]"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify(state.get_state())


@app.route("/api/toggle/<watcher>", methods=["POST"])
def api_toggle(watcher: str):
    ev = state.get_event(watcher)
    if ev is None:
        return jsonify({"error": "unknown watcher"}), 404

    if ev.is_set():
        ev.clear()
        log(f"{watcher} disabled", PREFIX)
    else:
        ev.set()
        log(f"{watcher} enabled", PREFIX)

    state.save_state()
    return jsonify(state.get_state())


@app.route("/api/logs")
def api_logs():
    after = request.args.get("after", 0, type=int)
    return jsonify(get_logs(after))


@app.route("/api/restart", methods=["POST"])
def api_restart():
    log("Restarting…", PREFIX, "warning")
    threading.Timer(0.3, lambda: os.execv(sys.executable, [sys.executable] + sys.argv)).start()
    return jsonify({"restarting": True})


@app.route("/api/organize", methods=["POST"])
def api_organize():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "path is required"}), 400
    threading.Thread(target=organize, args=(Path(path),), daemon=True).start()
    return jsonify({"started": True, "path": path})
