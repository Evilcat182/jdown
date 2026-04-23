# JDownloader + VPN + Bot Docker Setup

This stack provides a fully automated, VPN-routed download pipeline:

- **gluetun** — routes all traffic through a VPN (NordVPN/OpenVPN), acts as the shared network namespace for all services
- **firefox** — containerized browser with AdBlock and the JDownloader extension pre-installed, so Click & Load works out of the box
- **jdownloader** — download manager, accessible via web UI, all traffic goes through the VPN
- **jdown-bot** — Python automation layer that auto-starts downloads, organizes finished files into movie/series destinations, renames them, and triggers a Plex media scan on success

## 1. Create .env

Create a .env file next to docker-compose.yml.

```env
OPENVPN_USER=
OPENVPN_PASSWORD=
WEB_AUTHENTICATION_PASSWORD=
PREMIUM_ACCOUNT_HOSTER=
PREMIUM_ACCOUNT_USERNAME=
PREMIUM_ACCOUNT_PASSWORD=
EXTRACTION_PASSWORDS=
MOVIE_DESTINATION=
SERIES_DESTINATION=
DOWNLOADS_PATH=
PLEX_API_ROOT=
PLEX_TOKEN=
FF_OPEN_URL=
DEBUG=0
```

Required:

- OPENVPN_USER — NordVPN OpenVPN username
- OPENVPN_PASSWORD — NordVPN OpenVPN password
- WEB_AUTHENTICATION_PASSWORD — password for JDownloader web UI
- DOWNLOADS_PATH — host path where downloads are stored
- MOVIE_DESTINATION — host path where organized movies are moved
- SERIES_DESTINATION — host path where organized series are moved

Optional:

- PREMIUM_ACCOUNT_HOSTER — hoster domain, e.g. rapidgator.net
- PREMIUM_ACCOUNT_USERNAME — premium account username
- PREMIUM_ACCOUNT_PASSWORD — premium account password
- EXTRACTION_PASSWORDS — comma-separated list of archive passwords
- PLEX_API_ROOT — Plex server URL, e.g. http://plex:32400
- PLEX_TOKEN — Plex authentication token
- FF_OPEN_URL — URL(s) Firefox opens on start; separate multiple with `|`
- DEBUG — set to `1` to enable verbose debug logging (default: `0`)

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

```text
https://HOST-IP:5800
```

Login:

- Username: admin
- Password: value from WEB_AUTHENTICATION_PASSWORD

## 4. Access Firefox

Open:

```text
http://HOST-IP:5801
```

The browser has AdBlock and the JDownloader extension pre-installed. Use it to browse download sites — Click & Load will send links directly to JDownloader.

## 5. Access jdown-bot Settings

Open:

```text
http://HOST-IP:8080
```

From here you can enable or disable:

- **Autostart Downloads** — automatically start downloading grabbed links
- **Auto organize when finished** — rename and move completed downloads to their destination
- **Invoke Plex Media Scan** — trigger a Plex library scan after a successful download
- **Delete downloaded source** — remove the source folder after a successful copy
- **Auto-answer Dialogs** — automatically confirm JDownloader dialogs (e.g. external link requests)
