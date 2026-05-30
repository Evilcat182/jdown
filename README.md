# JDownloader + VPN + Bot Docker Setup

This stack provides a fully automated, VPN-routed download pipeline:

- **gluetun** — routes all traffic through a VPN (NordVPN/OpenVPN), acts as the shared network namespace for all services
- **firefox** — containerized browser with AdBlock and the JDownloader extension pre-installed, so Click & Load works out of the box
- **jdownloader** — download manager, accessible via web UI, all traffic goes through the VPN
- **jdown-bot** — Python automation layer that auto-starts downloads, organizes finished files into movie/series destinations, renames them, and triggers a Plex media scan on success

## 1. Create .env

Create a `.env` file next to `docker-compose.yml`.

```env
# VPN (required)
OPENVPN_USER=
OPENVPN_PASSWORD=

# JDownloader web UI authentication (optional)
WEB_AUTHENTICATION_USERNAME=admin
WEB_AUTHENTICATION_PASSWORD=

# Host paths (required)
DOWNLOADS_PATH=
MOVIE_DESTINATION=
SERIES_DESTINATION=

# Premium download account (optional)
PREMIUM_ACCOUNT_HOSTER=
PREMIUM_ACCOUNT_USERNAME=
PREMIUM_ACCOUNT_PASSWORD=

# Archive extraction passwords, comma-separated (optional)
EXTRACTION_PASSWORDS=

# Plex integration (optional)
PLEX_API_ROOT=
PLEX_TOKEN=
PLEX_MOVIE_LIB_NAME=
PLEX_SHOW_LIB_NAME=

# Firefox startup URL(s), separated by | (optional)
FF_OPEN_URL=

# Verbose debug logging, set to 1 to enable (default: 0)
DEBUG=0

# HTTP proxy credentials for gluetun (optional)
PROXY_USER=
PROXY_PASSWORD=
```

### Required variables

| Variable | Description |
|---|---|
| `OPENVPN_USER` | NordVPN OpenVPN username |
| `OPENVPN_PASSWORD` | NordVPN OpenVPN password |
| `DOWNLOADS_PATH` | Host path where JDownloader saves files |
| `MOVIE_DESTINATION` | Host path where organized movies are placed |
| `SERIES_DESTINATION` | Host path where organized series are placed |

### Optional variables

| Variable | Description |
|---|---|
| `WEB_AUTHENTICATION_USERNAME` | JDownloader web UI username (default: `admin`) |
| `WEB_AUTHENTICATION_PASSWORD` | JDownloader web UI password |
| `PREMIUM_ACCOUNT_HOSTER` | Hoster domain, e.g. `rapidgator.net` |
| `PREMIUM_ACCOUNT_USERNAME` | Premium account username |
| `PREMIUM_ACCOUNT_PASSWORD` | Premium account password |
| `EXTRACTION_PASSWORDS` | Comma-separated list of archive passwords |
| `PLEX_API_ROOT` | Plex server URL, e.g. `http://plex:32400` |
| `PLEX_TOKEN` | Plex authentication token |
| `PLEX_MOVIE_LIB_NAME` | Plex movie library name to scan |
| `PLEX_SHOW_LIB_NAME` | Plex TV show library name to scan |
| `FF_OPEN_URL` | URL(s) Firefox opens on start; separate multiple with `\|` |
| `DEBUG` | Set to `1` to enable verbose debug logging (default: `0`) |
| `PROXY_USER` | Username for the HTTP proxy (port 8888) |
| `PROXY_PASSWORD` | Password for the HTTP proxy (port 8888) |

## 2. Start the stack

Start all services:

```bash
docker compose up -d
```

Stop everything:

```bash
docker compose down
```

## 3. Access JDownloader

Open:

```
https://HOST-IP:5800
```

Login with the credentials set in `WEB_AUTHENTICATION_USERNAME` / `WEB_AUTHENTICATION_PASSWORD`.

## 4. Access Firefox

Open:

```
http://HOST-IP:5801
```

The browser has AdBlock and the JDownloader extension pre-installed. Use it to browse download sites — Click & Load will send links directly to JDownloader.

## 5. Access jdown-bot

Open:

```
http://HOST-IP:8080
```

The web UI has three sections:

### Downloads

Shows all active JDownloader packages with progress, speed, and ETA. Controls:

- **Start All / Stop All** — start or stop the download controller
- Per-package **Start**, **Stop**, and **Remove** buttons

### Scanner

Scans the output folder for finished (or unlinked) media folders. Folders still actively downloading are automatically excluded. For each detected folder:

- Media metadata (title, year, type, resolution, codec, etc.) is detected via guessit and can be edited before organizing
- **Organize** — copies the folder to the correct movie or series destination using the configured naming templates; errors are shown inline on the card
- **Remove** — deletes the folder and all its contents

### Settings / Automation toggles

| Toggle | Description |
|---|---|
| **Autostart Downloads** | Automatically start downloading grabbed links |
| **Auto organize when finished** | Rename and move completed downloads to their destination |
| **Invoke Plex Media Scan** | Trigger a Plex library scan after a successful organize |
| **Delete downloaded source** | Remove the source folder after a successful copy |
| **Auto-answer Dialogs** | Automatically confirm JDownloader dialogs (e.g. external link requests) |

## 6. Browsing through VPN

Some mobile first suckers like my friend lexar prefere the mobile browsing expirience, because they are unwilling to lift their lazy asses of the coach.
<br>Well fear no more lazy bastards ...<br>
The stack exposes an HTTP proxy on port **8888** (via gluetun, so all traffic goes through the VPN).

### 6.1 System-wide proxy

Configure your device's Wi-Fi proxy settings to route all traffic through the VPN:

| Field | Value |
|---|---|
| Host | `HOST-IP` |
| Port | `8888` |

**iOS:** Settings → Wi-Fi → tap your network → Configure Proxy → Manual  
**Android:** Settings → Wi-Fi → long-press your network → Modify → Advanced → Proxy → Manual

### 6.2 Browser proxy (Firefox)

To use the proxy only in Firefox without changing system settings, configure it via `about:config`:

| Preference | Value |
|---|---|
| `network.proxy.type` | `1` |
| `network.proxy.http` | `HOST-IP` |
| `network.proxy.http_port` | `8888` |
| `network.proxy.ssl` | `HOST-IP` |
| `network.proxy.ssl_port` | `8888` |
| `network.proxy.allow_hijacking_localhost` | `true` |

> **Note:** `network.proxy.allow_hijacking_localhost` must be `true` to allow Click & Load to work —  
> Firefox blocks proxy forwarding of `127.0.0.1` requests by default, regardless of other proxy settings.
