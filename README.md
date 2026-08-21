# Findog Legacy Adapter

A library for reading a legacy Findog workbook and passing its data to another
application, such as a FastAPI seeder. It does not write to the workbook or
perform reverse synchronization.

## Install from GitHub

In the consuming project, add a dependency that points to a specific commit or
tag:

```toml
# pyproject.toml
dependencies = [
  "findog-legacy-adapter @ git+https://github.com/findog-app/findog-legacy-core.git@v0.7.2",
]
```

## Use in a seeder

```python
from findog_legacy_adapter import load_payment_book_from_dropbox

payment_book = load_payment_book_from_dropbox(
    access_token=settings.dropbox_token,
    dropbox_path="/Payments.xlsm",
    monitored_sheets={"Home": ["C", "I", "O"]},
)

for item in payment_book.payment_list:
    # item.payment, item.category, and item.sheet are legacy objects
    seed_payment(item.payment)
```

If your API has already downloaded the file, no Dropbox connection is needed:

```python
from findog_legacy_adapter import load_payment_book

payment_book = load_payment_book(workbook_bytes, {"Home": ["C", "I", "O"]})
```

## Development CLI

The CLI is only for manually checking the adapter. First copy
`config/config-example.yaml` to `config/config.yaml`; it contains
`excel_dropbox_path` and `monitored_sheets`. The token may be stored in `.env`:

```env
DROPBOX_API_KEY=your_token
```

```bash
uv run python main.py \
  --config config/config.yaml
```

`--dropbox-path` and `--monitored-sheets '{"Home": ["C"]}'` override their
YAML values. You can also set the config path through `CONFIG_PATH`.

Use `--interpret-codes` to read four-character category codes from header-cell
comments. Codes must contain at least two uppercase letters and be unique across
the monitored sheets. Invalid or duplicate codes are displayed as CLI errors.

## Test and build

```bash
uv run pytest -q
uv run python -m build
```
