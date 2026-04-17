#!/bin/sh
# Runs inside the jdownloader container before JD starts.
# Reads env vars and writes JDownloader config files.

JD_CFG="/config/cfg"
mkdir -p "$JD_CFG"

# --- Ensure /watch is writable for the app user ---
WATCH_DIR="/watch"
APP_UID="${USER_ID:-1000}"
APP_GID="${GROUP_ID:-1000}"

mkdir -p "$WATCH_DIR"

if [ -d "$WATCH_DIR" ]; then
  if chown -R "$APP_UID:$APP_GID" "$WATCH_DIR" 2>/dev/null; then
    chmod -R u+rwX,g+rwX "$WATCH_DIR" 2>/dev/null || true
    echo "init-jd-config: fixed permissions on $WATCH_DIR for $APP_UID:$APP_GID"
  else
    echo "init-jd-config: warning: could not chown $WATCH_DIR (host fs may restrict it)"
  fi
fi

# --- Extraction password list ---
if [ -n "$EXTRACTION_PASSWORDS" ]; then
  # Convert comma-separated passwords to JSON array
  echo "$EXTRACTION_PASSWORDS" | awk -F',' '{
    printf "["
    for (i=1; i<=NF; i++) {
      gsub(/^ +| +$/, "", $i)
      printf "\"%s\"", $i
      if (i < NF) printf ","
    }
    printf "]"
  }' > "$JD_CFG/org.jdownloader.extensions.extraction.ExtractionExtension.passwordlist.json"
  echo "init-jd-config: wrote extraction passwords"
fi