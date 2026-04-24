import os
import sys
import threading
from flask import Flask, jsonify, render_template, request
import state
from core import log, get_logs

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
