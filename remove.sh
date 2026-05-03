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

# Bring down the stack, remove named volumes and images
if [ -n "$COMPOSE" ]; then
    echo "reset: running $COMPOSE down --volumes --rmi all..."
    $COMPOSE down --volumes --rmi all
fi
