#!/bin/sh
# Runs inside the jdownloader container before JD starts.
# Reads env vars and writes JDownloader config files.

JD_CFG="/config/cfg"
mkdir -p "$JD_CFG"

# --- Remote API config ---
REMOTE_API_CFG="$JD_CFG/org.jdownloader.api.RemoteAPIConfig.json"

if [ -f "$REMOTE_API_CFG" ]; then
  if grep -q '"deprecatedapienabled"' "$REMOTE_API_CFG"; then
    # Force deprecated API enabled regardless of previous value.
    sed -i 's/"deprecatedapienabled":[[:space:]]*false/"deprecatedapienabled":true/g; s/"deprecatedapienabled":[[:space:]]*true/"deprecatedapienabled":true/g' "$REMOTE_API_CFG"
  else
    # If the key is missing, append it to the root object.
    sed -i 's/}[[:space:]]*$/,"deprecatedapienabled":true}/' "$REMOTE_API_CFG"
  fi
  # Disable localhost-only restriction.
  if grep -q '"deprecatedapilocalhostonly"' "$REMOTE_API_CFG"; then
    sed -i 's/"deprecatedapilocalhostonly":[[:space:]]*true/"deprecatedapilocalhostonly":false/g' "$REMOTE_API_CFG"
  else
    sed -i 's/}[[:space:]]*$/,"deprecatedapilocalhostonly":false}/' "$REMOTE_API_CFG"
  fi
else
  echo '{"deprecatedapienabled":true,"deprecatedapilocalhostonly":false}' > "$REMOTE_API_CFG"
fi