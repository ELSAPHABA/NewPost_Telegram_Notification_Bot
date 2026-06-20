#!/bin/sh
set -eu

: "${DATA_DIR:=/data}"
: "${CHAT_IDS_FILE:=${DATA_DIR}/chat_ids.json}"

export DATA_DIR CHAT_IDS_FILE

mkdir -p "$DATA_DIR" "$(dirname "$CHAT_IDS_FILE")"

if [ ! -f "$CHAT_IDS_FILE" ]; then
    printf '[]\n' > "$CHAT_IDS_FILE"
fi

if [ ! -e /app/chat_ids.json ]; then
    ln -s "$CHAT_IDS_FILE" /app/chat_ids.json
fi

exec "$@"
