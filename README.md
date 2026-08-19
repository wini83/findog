# Findog Legacy Adapter

Biblioteka do odczytu historycznego skoroszytu Findog i przekazania jego danych
do innej aplikacji, np. seedera FastAPI. Nie zapisuje skoroszytu ani nie
wykonuje synchronizacji zwrotnej.

## Instalacja z GitHub

W projekcie docelowym dodaj zależność wskazującą na konkretny commit lub tag:

```toml
# pyproject.toml
dependencies = [
  "findog-legacy-adapter @ git+https://github.com/TWOJ_LOGIN/findog-legacy-core.git@v0.7.2",
]
```

## Użycie w seederze

```python
from findog_legacy_adapter import load_payment_book_from_dropbox

payment_book = load_payment_book_from_dropbox(
    access_token=settings.dropbox_token,
    dropbox_path="/Oplaty.xlsm",
    monitored_sheets={"Home": ["C", "I", "O"]},
)

for item in payment_book.payment_list:
    # item.payment, item.category i item.sheet są obiektami legacy
    seed_payment(item.payment)
```

Jeżeli plik został już pobrany przez Twoje API, nie trzeba łączyć się z Dropbox:

```python
from findog_legacy_adapter import load_payment_book

payment_book = load_payment_book(workbook_bytes, {"Home": ["C", "I", "O"]})
```

## CLI developerskie

CLI służy wyłącznie do ręcznego sprawdzenia adaptera. Skopiuj najpierw
`config/config-example.yaml` do `config/config.yaml`; zawiera on
`excel_dropbox_path` i `monitored_sheets`. Token może być w `.env`:

```env
DROPBOX_API_KEY=twoj_token
```

```bash
uv run python main.py \
  --config config/config.yaml
```

`--dropbox-path` i `--monitored-sheets '{"Home": ["C"]}'` mogą nadpisać
wartości z YAML. Ścieżkę configu można też ustawić przez `CONFIG_PATH`.

## Testy i build

```bash
uv run pytest -q
uv run python -m build
```
