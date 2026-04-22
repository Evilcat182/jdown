# JDownloader + VPN + Bot Docker Setup

This stack runs three services:

- gluetun: VPN gateway and network namespace owner
- jdownloader: JDownloader UI/API, shares gluetun network stack
- jdown-bot: Python automation container that configures JDownloader and runs watchers

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
