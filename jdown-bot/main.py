import subprocess
import sys
import threading
from functions import log

# Run startup.py first (blocks until done)
log("Running startup.py...")
result = subprocess.run([sys.executable, "-u", "/app/startup.py"])
if result.returncode != 0:
    sys.exit(result.returncode)

# Import after startup so JDownloader is ready
import state
import watcher_linkgrabber
import watcher_downloads
import watcher_dialogs
import settings
from webui import app

log("Starting watchers...")
threading.Thread(
    target=watcher_linkgrabber.run,
    args=(state.linkgrabber_enabled,),
    daemon=True,
    name="watcher-linkgrabber",
).start()

threading.Thread(
    target=watcher_downloads.run,
    args=(state.downloads_enabled,),
    daemon=True,
    name="watcher-downloads",
).start()

threading.Thread(
    target=watcher_dialogs.run,
    args=(state.dialogs_enabled,),
    daemon=True,
    name="watcher-dialogs",
).start()

log("Starting web UI on port 8080...")
if settings.DEBUG:
    app.run(host="0.0.0.0", port=8080, debug=True)
else:
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
