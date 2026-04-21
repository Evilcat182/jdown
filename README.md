# JDownloader + VPN + Bot Docker Setup

This stack runs three services:

- gluetun: VPN gateway and network namespace owner
- jdownloader: JDownloader UI/API, shares gluetun network stack
- jdown-bot: Python automation container that configures JDownloader and runs watchers

## 1. Create .env

Create a .env file next to docker-compose.yml.

Example:

```env
OPENVPN_USER=your_nordvpn_username
OPENVPN_PASSWORD=your_nordvpn_password
WEB_AUTHENTICATION_PASSWORD=choose_a_strong_password
DOWNLOADS_PATH=/mnt/folder
EXTRACTION_PASSWORDS=password1,password2
PREMIUM_ACCOUNT_HOSTER=rapidgator.net
PREMIUM_ACCOUNT_USERNAME=your_username
PREMIUM_ACCOUNT_PASSWORD=your_password
```

Required:

- OPENVPN_USER
- OPENVPN_PASSWORD
- WEB_AUTHENTICATION_PASSWORD
- DOWNLOADS_PATH
- PREMIUM_ACCOUNT_HOSTER
- PREMIUM_ACCOUNT_USERNAME
- PREMIUM_ACCOUNT_PASSWORD

Optional:

- EXTRACTION_PASSWORDS

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
