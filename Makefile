SHELL := /bin/bash

.PHONY: ruff test build

ruff:
	uv run ruff check . --fix
	uv run ruff format .

test:
	uv run pytest -q

build:
	uv run python -m build
