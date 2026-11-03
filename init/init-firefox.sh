#!/bin/sh
# Runs inside the firefox container before Firefox starts.

# Find Firefox's distribution directory
FF_DIST=""
for candidate in /usr/lib/firefox/distribution /usr/lib64/firefox/distribution /usr/share/firefox/distribution; do
    if [ -d "$(dirname "$candidate")" ]; then
        FF_DIST="$candidate"
        break
    fi
done

if [ -z "$FF_DIST" ]; then
    echo "init-firefox: could not find Firefox distribution directory, skipping extension install"
    exit 0
fi

mkdir -p "$FF_DIST"

POLICIES_FILE="$FF_DIST/policies.json"

cat > "$POLICIES_FILE" << 'EOF'
{
  "policies": {
    "Preferences": {
      "network.lna.enabled": { "Value": false, "Status": "locked" },
      "network.lna.blocking": { "Value": false, "Status": "locked" }
    },
    "ExtensionSettings": {
      "{03e07985-30b0-4ae0-8b3e-0c7519b9bdf6}": {
        "installation_mode": "force_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/download-with-jdownloader/latest.xpi"
      },
      "adguardadblocker@adguard.com": {
        "installation_mode": "blocked"
      },
      "uBlock0@raymondhill.net": {
        "installation_mode": "force_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
      }
    },
    "3rdparty": {
      "Extensions": {
        "uBlock0@raymondhill.net": {
          "toOverwrite": {
            "trustedSiteDirectives": [
              "chrome-extension-scheme",
              "moz-extension-scheme",
              "filecrypt.cc",
              "filecrypt.co"
            ],
            "filters": [
              "@@||127.0.0.1:9666^",
              "@@||localhost:9666^"
            ]
          }
        }
      }
    }
  }
}
EOF

echo "init-firefox: wrote $POLICIES_FILE"
