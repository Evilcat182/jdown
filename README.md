# JDownloader + VPN + Bot Docker Setup

This stack provides a fully automated, VPN-routed download pipeline:

- **gluetun** — routes all traffic through a VPN (NordVPN/OpenVPN), acts as the shared network namespace for all services
- **firefox** — containerized browser with uBlock Origin and the JDownloader extension pre-installed, so Click & Load works out of the box
- **jdownloader** — download manager, accessible via web UI, all traffic goes through the VPN
- **jdown-bot** — Python automation layer that auto-starts downloads, organizes finished files into movie/series destinations, renames them, and triggers a Plex media scan on success

## 1. Create .env

Copy the example file next to `docker-compose.yml` and fill in the values:

```bash
cp .env.example .env
```

`.env` is gitignored, so your credentials stay out of the repository.

### Required variables

| Variable | Description |
|---|---|
| `OPENVPN_USER` | NordVPN OpenVPN username |
| `OPENVPN_PASSWORD` | NordVPN OpenVPN password |
| `GLUETUN_API_KEY` | API key for gluetun's control server, see [The gluetun API key](#the-gluetun-api-key) |
| `DOWNLOADS_PATH` | Host path where JDownloader saves files |
| `MOVIE_DESTINATION` | Host path where organized movies are placed |
| `SERIES_DESTINATION` | Host path where organized series are placed |

### The gluetun API key

`GLUETUN_API_KEY` is a shared secret between gluetun and jbot, and you can choose any value:

- **gluetun** gets it via `HTTP_CONTROL_SERVER_AUTH_DEFAULT_ROLE` and only answers control-server requests (port 8000) that send this key.
- **jbot** sends it in the `X-API-Key` header to show the VPN status and switch the VPN server.

Both are filled from the same `.env` entry, so they always match. `docker compose up` stops with an error if it is missing.

Use letters and digits only (no `"`, `\` or `$`, which would break the JSON value or Compose's variable syntax), ideally 20+ characters. To generate one:

```bash
openssl rand -hex 16
```

Port 8000 is not published to the host, so only containers in the stack's network can reach the control server. After changing the key, recreate the whole stack, because restarting gluetun also cuts the network of Firefox and JDownloader:

```bash
docker compose down && docker compose up -d
```

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

The browser has uBlock Origin (with a built-in exception for Click & Load) and the JDownloader extension pre-installed. Use it to browse download sites — Click & Load will send links directly to JDownloader.

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

### Settings / VPN

Shows the VPN status and public IP, and lets you switch the VPN country (and optionally city) at runtime. Gluetun reconnects in place, so JDownloader and Firefox keep running; active downloads resume automatically.

The choice is saved in jbot's config and re-applied whenever gluetun runs with something else, e.g. after a container restart with the `SERVER_COUNTRIES` default from `docker-compose.yml`. The country/city list comes from gluetun's server list, which is refreshed every 24h (`UPDATER_PERIOD`) and kept in the `jdown_config_gluetun` volume.

A switch only counts once the new tunnel is up. If a server doesn't connect within 20 s, jbot has gluetun try another server in that country. After 3 failed servers it switches back to the previous one and doesn't save the new choice. If the VPN drops at runtime and stays down for 2 minutes, jbot reconnects, and gluetun then picks a different server in the same country.

#### Switching often fails / `TLS key negotiation failed` / `ENETUNREACH`

The server list built into the gluetun image can be years old, so many of its IPs no longer exist. On a fresh volume, or if switches keep failing, update the list manually. This runs outside the VPN, so it also works while the tunnel is down. Then restart the stack so gluetun loads the new list:

```bash
sudo podman run --rm --volumes-from gluetun qmcgaw/gluetun:v3.41.3 update -enduser -providers nordvpn
sudo podman restart gluetun && sudo podman restart jdownloader firefox jbot
```

`AUTH_FAILED` in the gluetun log means the server rejects your service credentials. That's on NordVPN's side, and jbot can't fix it. If it happens for every server in a country, pick a different country.

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

## 7. Development

By default jbot runs the code baked into its image, so after changing anything under `jbot/` you need to rebuild:

```bash
docker compose up -d --build jbot
```

For faster iteration, mount the source into the container instead:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

Compose automatically merges `docker-compose.override.yml` on top of `docker-compose.yml`, so code changes then only need `docker compose restart jbot`. The override file is gitignored. To run without it (e.g. to test the production setup), name the file explicitly: `docker compose -f docker-compose.yml up -d`.
