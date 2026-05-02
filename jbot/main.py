import subprocess
import sys
import threading

from core import log

# Run startup.py first (blocks until done)
log("Running startup.py...")
result = subprocess.run([sys.executable, "-u", "/app/startup.py"])
if result.returncode != 0:
    sys.exit(result.returncode)

# Import after startup so JDownloader is ready
import config
from watchers import dialogs, downloads, linkgrabber
from web import app

log("Starting watchers...")
threading.Thread(
    target=linkgrabber.run,
    args=(config.get_event("linkgrabber"),),
    daemon=True,
    name="watcher-linkgrabber",
).start()

threading.Thread(
    target=downloads.run,
    args=(config.get_event("downloads"),),
    daemon=True,
    name="watcher-downloads",
).start()

threading.Thread(
    target=dialogs.run,
    args=(config.get_event("dialogs"),),
    daemon=True,
    name="watcher-dialogs",
).start()

log("Starting web UI on port 8080...")
if config.get_config("debug"):
    app.run(host="0.0.0.0", port=8080, debug=True)
else:
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
