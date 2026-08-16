FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC \
    DATA_DIR=/data \
    CHAT_IDS_FILE=/data/chat_ids.json

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser \
    && apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY *.py ./
COPY user-agents.txt ./
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && mkdir -p /data \
    && chmod +x /usr/local/bin/docker-entrypoint.sh \
    && chown -R appuser:appuser /app /data

VOLUME ["/data"]

USER appuser

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "main.py"]
