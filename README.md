# JDownloader Docker Setup

## 1. Create `.env`

Create a `.env` file in the same directory as `docker-compose.yml`.

Example:

```env
OPENVPN_USER=your_nordvpn_username
OPENVPN_PASSWORD=your_nordvpn_password
WEB_AUTHENTICATION_PASSWORD=choose_a_strong_password
DOWNLOADS_PATH=/mnt/folder
EXTRACTION_PASSWORDS=password1,password2
```

Required values:

- `OPENVPN_USER`
- `OPENVPN_PASSWORD`
- `WEB_AUTHENTICATION_PASSWORD`
- `DOWNLOADS_PATH`

`EXTRACTION_PASSWORDS` is optional.

## 2. Start the containers

Run:

```bash
docker compose up -d
```

To update after changes:

```bash
docker compose up -d --force-recreate
```

To stop everything:

```bash
docker compose down
```

## 3. Open JDownloader

Open:

```text
https://CONTAINER-IP:5800
```

Use:

- Username: `admin`
- Password: the value from `WEB_AUTHENTICATION_PASSWORD`
