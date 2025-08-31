#!/usr/bin/env bash
set -euo pipefail

# Default to YAML config used by Settings.from_all()
: "${CONFIG_PATH:=/config/config.yaml}"
SEED_SRC="/app/config/config-example.yaml"

if [ ! -f "$CONFIG_PATH" ]; then
  echo ">> No config at $CONFIG_PATH, seeding from example"
  mkdir -p "$(dirname "$CONFIG_PATH")"
  if [ -f "$SEED_SRC" ]; then
    cp "$SEED_SRC" "$CONFIG_PATH"
  else
    echo "!! Missing seed file at $SEED_SRC" >&2
  fi
fi

exec "$@"
