from flask import Flask, jsonify, render_template
import state

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "linkgrabber": state.linkgrabber_enabled.is_set(),
        "downloads":   state.downloads_enabled.is_set(),
    })


@app.route("/api/toggle/<watcher>", methods=["POST"])
def api_toggle(watcher: str):
    if watcher == "linkgrabber":
        ev = state.linkgrabber_enabled
    elif watcher == "downloads":
        ev = state.downloads_enabled
    else:
        return jsonify({"error": "unknown watcher"}), 404

    if ev.is_set():
        ev.clear()
        print(f"[WebUI] {watcher} watcher disabled")
    else:
        ev.set()
        print(f"[WebUI] {watcher} watcher enabled")

    return jsonify({
        "linkgrabber": state.linkgrabber_enabled.is_set(),
        "downloads":   state.downloads_enabled.is_set(),
    })
