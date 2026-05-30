FROM python:3.12-slim

RUN groupadd -g 1000 app && useradd -u 1000 -g app -s /bin/sh -m app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh && chown -R app:app /app \
    && mkdir -p /config /output /data/movies /data/series \
    && chown app:app /config /output /data/movies /data/series

USER app

ENTRYPOINT ["/app/entrypoint.sh"]
