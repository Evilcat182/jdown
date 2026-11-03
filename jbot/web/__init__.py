import os
import sys
import threading
import config
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from core import log, get_logs
from media import progress
from media.organizer import organize, _guessit


def _serialize_guessit(info: dict) -> dict:
    """Convert a guessit result dict to plain JSON-serializable types."""
    result = {}
    for k, v in info.items():
        if isinstance(v, (str, int, float, bool, type(None))):
            result[k] = v
        elif isinstance(v, list):
            result[k] = [i if isinstance(i, (str, int, float, bool, type(None))) else str(i) for i in v]
        else:
            result[k] = str(v)
    return result

app = Flask(__name__)

PREFIX = "[WebUI]"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/api/status")
def api_status():
    return jsonify(config.get_state())


@app.route("/api/toggle/<watcher>", methods=["POST"])
def api_toggle(watcher: str):
    ev = config.get_event(watcher)
    if ev is None:
        return jsonify({"error": "unknown watcher"}), 404

    if ev.is_set():
        ev.clear()
        log(f"{watcher} disabled", PREFIX)
    else:
        ev.set()
        log(f"{watcher} enabled", PREFIX)
    config.set_config(watcher,ev.is_set())
    return jsonify(config.get_state())


@app.route("/api/logs")
def api_logs():
    after = request.args.get("after", 0, type=int)
    return jsonify(get_logs(after))


@app.route("/api/restart", methods=["POST"])
def api_restart():
    log("Restarting…", PREFIX, "warning")
    threading.Timer(0.3, lambda: os.execv(sys.executable, [sys.executable] + sys.argv)).start()
    return jsonify({"restarting": True})


@app.route("/api/scan")
def api_scan():
    scan_dir = Path(config.get_config("scan_path"))
    if not scan_dir.is_dir():
        return jsonify({"error": f"Scan path '{scan_dir}' not found"}), 404

    # Determine which top-level subdirs to skip (e.g. the organised destinations)
    skip_tops: set[Path] = set()
    for dest_key in ("movie_destination", "series_destination"):
        dest = config.get_config(dest_key)
        if not dest:
            continue
        dest_path = Path(dest)
        try:
            rel = dest_path.relative_to(scan_dir)
            skip_tops.add(scan_dir / rel.parts[0])
        except ValueError:
            pass

    # Determine which top-level subdirs are still being downloaded (not finished)
    active_download_dirs: set[Path] = set()
    try:
        from core.jdownloader import jdown_downloads_get_status, jdown_package_is_finished
        for pkg in jdown_downloads_get_status():
            if not pkg.get("save_to"):
                continue
            if jdown_package_is_finished(pkg["uuid"], pkg.get("status")):
                continue  # Finished — allow it to appear in scan
            save_path = Path(pkg["save_to"])
            try:
                rel = save_path.relative_to(scan_dir)
                active_download_dirs.add(scan_dir / rel.parts[0])
            except ValueError:
                # save_to is outside scan_dir — match directly
                active_download_dirs.add(save_path)
    except Exception:
        pass

    results = []
    for entry in sorted(scan_dir.iterdir()):
        if not entry.is_dir() or entry in skip_tops:
            continue
        if entry in active_download_dirs:
            continue  # Still downloading — exclude from scan
        try:
            info = _serialize_guessit(dict(_guessit(entry.name)))
        except Exception:
            info = {}
        results.append({
            "path": str(entry),
            "name": entry.name,
            "type": info.get("type"),
            "has_confidence": bool(set(config.get_config("media_confidence_fields")).intersection(info)),
            "info": info,
        })

    return jsonify(results)


@app.route("/api/scan/folder", methods=["DELETE"])
def api_scan_folder_delete():
    data = request.get_json(silent=True) or {}
    target = data.get("path", "").strip()
    if not target:
        return jsonify({"error": "No path provided"}), 400

    scan_dir = Path(config.get_config("scan_path")).resolve()
    target_path = Path(target).resolve()

    # Safety: must be a direct child of scan_dir (no traversal, not the root itself)
    try:
        rel = target_path.relative_to(scan_dir)
    except ValueError:
        return jsonify({"error": "Path is outside scan directory"}), 403
    if len(rel.parts) != 1:
        return jsonify({"error": "Only top-level scan folders may be deleted"}), 403
    if not target_path.is_dir():
        return jsonify({"error": "Path is not a directory"}), 400

    import shutil
    shutil.rmtree(target_path)
    log(f"Deleted folder '{target_path.name}'", PREFIX)
    return jsonify({"ok": True})


@app.route("/api/downloads")
def api_downloads():
    from core.jdownloader import jdown_downloads_get_status, jdown_downloads_get_state
    return jsonify({
        "controller_state": jdown_downloads_get_state(),
        "packages": jdown_downloads_get_status(),
    })


@app.route("/api/downloads/start", methods=["POST"])
def api_downloads_start():
    from core.jdownloader import jdown_downloads_start
    return jsonify({"ok": jdown_downloads_start()})


@app.route("/api/downloads/stop", methods=["POST"])
def api_downloads_stop():
    from core.jdownloader import jdown_downloads_stop
    return jsonify({"ok": jdown_downloads_stop()})


@app.route("/api/downloads/<int:pkg_uuid>/start", methods=["POST"])
def api_pkg_start(pkg_uuid: int):
    from core.jdownloader import jdown_package_force_start
    return jsonify({"ok": jdown_package_force_start(pkg_uuid)})


@app.route("/api/downloads/<int:pkg_uuid>/stop", methods=["POST"])
def api_pkg_stop(pkg_uuid: int):
    from core.jdownloader import jdown_package_stop
    return jsonify({"ok": jdown_package_stop(pkg_uuid)})


@app.route("/api/downloads/<int:pkg_uuid>", methods=["DELETE"])
def api_pkg_remove(pkg_uuid: int):
    from core.jdownloader import jdown_package_remove
    return jsonify({"ok": jdown_package_remove(pkg_uuid)})


@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    return jsonify(config.get_ui_values())


@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    data = request.get_json(silent=True) or {}
    errors = {}
    for key, value in data.items():
        try:
            config.set_config(key, value)
        except KeyError:
            errors[key] = "unknown key"
        except Exception as exc:
            errors[key] = str(exc)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    log("Settings updated via WebUI", PREFIX)
    return jsonify({"ok": True})


@app.route("/api/organize", methods=["POST"])
def api_organize():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "path is required"}), 400

    # Safety: must be a direct child of scan_dir (organize may delete the source)
    scan_dir = Path(config.get_config("scan_path")).resolve()
    target_path = Path(path).resolve()
    try:
        rel = target_path.relative_to(scan_dir)
    except ValueError:
        return jsonify({"error": "Path is outside scan directory"}), 403
    if len(rel.parts) != 1:
        return jsonify({"error": "Only top-level scan folders may be organized"}), 403

    info_override = data.get("info") or None
    errors = organize(target_path, info_override=info_override)
    return jsonify({"errors": errors or []})


@app.route("/api/organize/progress")
def api_organize_progress():
    path = request.args.get("path", "").strip()
    if path:
        job = progress.get_job(path)
        if not job:
            return jsonify({"active": False})
        total = job["total_bytes"]
        percent = round(min(100.0, job["copied_bytes"] / total * 100), 1) if total > 0 else 100.0
        return jsonify({"active": True, "percent": percent, **job})
    # No path: return all active copy jobs (used by the UI to survive reloads)
    jobs = []
    for p, job in progress.get_all_jobs().items():
        total = job["total_bytes"]
        percent = round(min(100.0, job["copied_bytes"] / total * 100), 1) if total > 0 else 100.0
        jobs.append({"path": p, "percent": percent, **job})
    return jsonify({"active": bool(jobs), "jobs": jobs})


@app.route("/api/vpn")
def api_vpn():
    from core.gluetun import (
        gluetun_is_configured, gluetun_get_settings, gluetun_get_status,
        gluetun_get_public_ip, gluetun_get_locations,
    )
    selected = {"country": config.get_config("vpn_country"), "city": config.get_config("vpn_city")}
    if not gluetun_is_configured():
        return jsonify({"configured": False, "selected": selected})

    settings = gluetun_get_settings()
    if settings is None:
        return jsonify({"configured": True, "reachable": False, "selected": selected})

    provider = (settings.get("provider") or {}).get("name") or ""
    selection = (settings.get("provider") or {}).get("server_selection") or {}
    return jsonify({
        "configured": True,
        "reachable":  True,
        "status":     gluetun_get_status(),
        "public_ip":  gluetun_get_public_ip(),
        "provider":   provider,
        "current":    {"countries": selection.get("countries") or [], "cities": selection.get("cities") or []},
        "selected":   selected,
        "locations":  gluetun_get_locations(provider, settings.get("type") or ""),
    })


@app.route("/api/vpn", methods=["POST"])
def api_vpn_set():
    from core.gluetun import gluetun_is_configured, gluetun_get_settings, gluetun_get_locations, gluetun_set_server_selection
    if not gluetun_is_configured():
        return jsonify({"ok": False, "error": "GLUETUN_API_KEY is not set"}), 400

    data = request.get_json(silent=True) or {}
    country = (data.get("country") or "").strip()
    city = (data.get("city") or "").strip()
    if not country:
        return jsonify({"ok": False, "error": "country is required"}), 400

    # Validate against the server list when it is available (gluetun validates too)
    settings = gluetun_get_settings() or {}
    provider = (settings.get("provider") or {}).get("name") or ""
    locations = gluetun_get_locations(provider, settings.get("type") or "") if provider else None
    if locations is not None:
        if country not in locations:
            return jsonify({"ok": False, "error": f"Unknown country '{country}'"}), 400
        if city and city not in locations[country]:
            return jsonify({"ok": False, "error": f"Unknown city '{city}' in {country}"}), 400

    ok, message = gluetun_set_server_selection(country, city)
    if not ok:
        return jsonify({"ok": False, "error": message}), 502

    # Persist only after gluetun accepted it, the VPN watcher re-applies it after restarts
    config.patch_config({"vpn_country": country, "vpn_city": city})
    target = f"{country}/{city}" if city else country
    log(f"VPN server changed to '{target}'", PREFIX)
    return jsonify({"ok": True, "message": message})
