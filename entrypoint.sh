#!/usr/bin/env bash
set -e
: "${CONFIG_PATH:=/config/config.py}"
if [ ! -f "$CONFIG_PATH" ]; then
  echo ">> No config at $CONFIG_PATH, seeding from config-example.py"
  mkdir -p "$(dirname "$CONFIG_PATH")"
  cp /app/config-example.py "$CONFIG_PATH"
fi
exec "$@"
