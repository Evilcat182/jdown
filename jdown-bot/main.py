import subprocess
import sys
import threading

# Run startup.py first (blocks until done)
print("Running startup.py...")
result = subprocess.run([sys.executable, "-u", "/app/startup.py"])
if result.returncode != 0:
    sys.exit(result.returncode)

# Import after startup so JDownloader is ready
import state
import watcher_linkgrabber
import watcher_downloads
from webui import app

print("Starting watchers...")
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

print("Starting web UI on port 8080...")
app.run(host="0.0.0.0", port=8080)
