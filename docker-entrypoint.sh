#!/bin/sh
set -eu

mkdir -p /data

if [ ! -e /app/chat_ids.json ]; then
    ln -s /data/chat_ids.json /app/chat_ids.json
fi

if [ ! -f /data/chat_ids.json ]; then
    printf '[]\n' > /data/chat_ids.json
fi

exec "$@"
