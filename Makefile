SHELL := /bin/bash

.PHONY: dev ruff

dev:
	@test -f .env || { echo "Brak pliku .env" >&2; exit 1; }
	@set -a; . ./.env; set +a; uv run python main.py --enable-api-all --enable-dropbox

ruff:
	uv run ruff check . --fix
	uv run ruff format .
