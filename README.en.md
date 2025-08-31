# Findog

[Polski](README.md) | English

Automatic home payments assistant: fetches amounts and due dates from several services, updates an Excel workbook stored in Dropbox, reminds you about upcoming deadlines (Pushover), sends an e‑mail summary, and optionally generates simple analytics.

[![CI: Pylint](https://github.com/wini83/findog/actions/workflows/pylint.yml/badge.svg)](https://github.com/wini83/findog/actions/workflows/pylint.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)


## Features
- Read/write Excel workbook (`Oplaty.xlsm`) to/from Dropbox.
- Integrations: eKartoteka (rent/HOA), Enea (electricity), iPrzedszkole, nju (mobile invoices).
- Pushover reminders for overdue and urgent payments (≤2 days).
- E‑mail (Gmail) daily summary with the next payments list.
- Simple Analytics module generating a PNG chart for the current month.
- Pipeline built as a Chain of Responsibility.


## Quick Start (Docker Compose)
1) Configure `config/config.yaml` (copy from `config/config-example.yaml`).
2) Create secret files under `secrets/` (see the list below).
3) Start the service:

```bash
docker compose up --build
```

The default command is: `python main.py --enable-all`.


### Required secrets (Docker)
Files placed under `secrets/` and mounted as Docker secrets:
- `dropbox_apikey`
- `pushover_apikey`
- `pushover_user`
- `ekartoteka_password`
- `enea_password`
- `przedszkole_password`
- `gmail_password`
- `nju_<PHONE_NUMBER>_password` (for every Nju account configured in YAML)

Compose already contains example entries under `secrets:` and mounts them in `services.findog.secrets`.


## Configuration
Configuration is composed from YAML (file) + Docker secrets + environment variables.

- Config file path: `CONFIG_PATH` (defaults to `/config/config.yaml`).
- Data and logs: `DATA_DIR` (defaults to `/data`).
- For development you may override Dropbox key via ENV: set `ALLOW_ENV_DROPBOX=1` and provide `DROPBOX_API_KEY=...`.

Example snippet from `config/config.yaml`:

```yaml
excel_local_path: "/data/Oplaty.xlsm"
excel_dropbox_path: "/Oplaty.xlsm"

monitored_sheets:
  "Ania & Mario": ["C","I","O","R","U","X","AD","AG","AJ","AM","AP"]
  "Mama": ["C","I"]

# logins (passwords come from Docker secrets)
ekartoteka:   { username: "user@server.com" }
enea:         { username: "user@server.com" }
przedszkole:  { kindergarten: "p_city", username: "rodzic_123456" }

# mapping where to update values in Excel
ekartoteka_sheet: ["Main", "Mieszkanie czynsz"]
przedszkole_sheet: ["Main", "Kindergarten George"]
enea_sheet:        ["Main", "Prąd Enea"]

# e‑mail notifications
gmail_user: "noreply@server.com"
recipients: ["u1@server.com","u2@server.com"]

# multiple Nju accounts
nju_credentials:
  - { phone: "601200300", sheet: "Greg",   cat: "Telefon a" }
  - { phone: "602200300", sheet: "Joanna", cat: "Telefon b" }
```

You can override YAML values per‑key using Pydantic nested ENV vars, e.g.:
`E_KARTOTEKA__USERNAME=another_name`.


## Running (CLI)
The app uses Click and lets you enable specific stages/integrations.

Common modes:
- `--enable-all` — full pipeline: Dropbox + APIs + notifications + analytics.
- `--enable-dropbox` — work with Excel (download → process → save → upload back).
- `--enable-notification` — Pushover + e‑mail.
- `--enable-analytics` — generate charts/HTML summary.
- `--enable-api-all` or `--enable-api <name>` — enable all or selected integrations (`ekartoteka`, `iprzedszkole`, `enea`, `nju`).
- `--disable-commit` — do not upload the file back to Dropbox (local save only).

Examples:

```bash
# Full run (also the docker-compose default)
python main.py --enable-all

# Only integrations + logs, without touching the Excel file
python main.py --enable-api-all --enable-notification

# Local debugging: work on the file and skip Dropbox commit
python main.py --enable-dropbox --disable-commit
```


## Architecture (at a glance)
- "Chain of Responsibility" pattern — modules as Handlers:
  - `FileDownloadHandler` → `FileProcessHandler` → integrations (`eKartoteka`, `Enea`, `iPrzedszkole`, `nju`) → `NotifyOngoingHandler` → `MailingHandler` → `AnalyticsHandler` → `SaveFileLocallyHandler` → `FileCommitHandler`.
- Central context (`HandlerContext`) holds clients (Dropbox, Pushover), configured paths and the `PaymentBook`.
- `PaymentBook` maps workbook sheets/categories to current‑month payments and updates the relevant cells.

Logs are stored under `DATA_DIR/logs/findog.log`. Additional artifacts:
- `/data/output.png` (Analytics),
- `/data/output_mail.html` (mail preview when sending is disabled).


## Local run (without Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export CONFIG_PATH="$PWD/config/config.yaml"
export DATA_DIR="$PWD/data"
# (optional for dev)
export ALLOW_ENV_DROPBOX=1
export DROPBOX_API_KEY="..."
python main.py --enable-all
```

Note: Prefer Docker secrets for passwords/tokens. In local mode you may place files under `secrets/` or provide your own ENV handling.


## Screenshots
- Mail preview: the HTML generated by the Mail module (when enabled in preview mode) is saved as `/data/output_mail.html`.
- Current month chart: `/data/output.png` when run with `--enable-analytics`.

Tip: to generate artifacts locally without committing the file back to Dropbox:

```bash
python main.py --enable-dropbox --enable-api-all --enable-analytics --disable-commit
```

Project logo:

![Findog Logo](templates/findog_logo.png)


## Terminology
- "eKartoteka" — rent/HOA integration (in code: `EkartotekaHandler`).
- "iPrzedszkole" — kindergarten system integration.
- "nju" — nju (mobile) billing integration.
- "Analytics" — simple PNG chart generator.


## Security & best practices
- Never commit anything from `secrets/` (repo ships with a `.gitignore`).
- Store secrets as Docker secrets. Do not keep them in YAML/README.
- Use a Dropbox API key with minimal scope.
- Keep the Excel file versioned (Dropbox history).


## Development
- Logging: `loguru`.
- Linting: Pylint workflow (GitHub Actions) is included.
- Tests: simple unit tests for handlers are available under `tests/`. To run locally you need `pytest` (not included in `requirements.txt`).

```bash
pip install pytest
pytest -q
```

---
Questions or want to extend the README (e.g., screenshots, sample workbook)? Feel free to open an issue or PR.
