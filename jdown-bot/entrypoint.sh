#!/bin/sh
set -e

export PYTHONUNBUFFERED=1

echo "Running startup.py..."
python -u /app/startup.py

echo "Starting watchers..."
python -u /app/watcher_linkgrabber.py &
python -u /app/watcher_downloads.py &

wait
