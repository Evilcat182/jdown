#!/bin/sh
# Runs inside the jdownloader container before JD starts.
# Reads env vars and writes JDownloader config files.

JD_CFG="/config/cfg"
mkdir -p "$JD_CFG"

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