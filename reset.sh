#!/bin/sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Detect compose command
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1; then
    COMPOSE="podman compose"
else
    echo "reset: neither 'docker compose' nor 'podman compose' found, skipping stack teardown"
    COMPOSE=""
fi

# Bring down the stack if it is running
if [ -n "$COMPOSE" ]; then
    echo "reset: running $COMPOSE down..."
    $COMPOSE down
fi

# Delete all contents of config dirs except .gitkeep
for DIR in config/jdownloader config/firefox config/jbot; do
    if [ -d "$DIR" ]; then
        echo "reset: clearing $DIR (keeping .gitkeep)..."
        find "$DIR" -mindepth 1 -not -name ".gitkeep" -delete 2>/dev/null || true
    fi
done

echo "reset: done."
