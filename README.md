# Findog

[Polski](README.md) | [English](README.en.md)

Automatyczny asystent domowych płatności: pobiera kwoty i terminy z kilku serwisów, aktualizuje skoroszyt Excel w Dropbox, przypomina o zbliżających się terminach (Pushover), wysyła podsumowanie e‑mailem i opcjonalnie generuje prostą analitykę.

[![CI: Pylint](https://github.com/wini83/findog/actions/workflows/pylint.yml/badge.svg)](https://github.com/wini83/findog/actions/workflows/pylint.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)


## Funkcje
- Zapis/odczyt skoroszytu Excel (`Oplaty.xlsm`) z/do Dropbox.
- Integracje: eKartoteka (czynsz), Enea (prąd), iPrzedszkole, nju (faktury tel.).
- Przypomnienia Pushover o zaległych i pilnych płatnościach (≤2 dni).
- E‑mail (Gmail) z dziennym podsumowaniem i listą najbliższych płatności.
- Prosty moduł Analytics generujący wykres PNG bieżącego miesiąca.
- Uruchamianie etapów w łańcuchu „Handlerów” (Chain of Responsibility).


## Szybki start (Docker Compose)
1) Skonfiguruj plik `config/config.yaml` (możesz skopiować z `config/config-example.yaml`).
2) Utwórz pliki z sekretami w katalogu `secrets/` (patrz lista niżej). 
3) Uruchom usługę:

```bash
docker compose up --build
```

Domyślna komenda startowa to: `python main.py --enable-all`.


### Wymagane sekrety (Docker)
Pliki w katalogu `secrets/` mapowane jako Docker secrets:
- `dropbox_apikey`
- `pushover_apikey`
- `pushover_user`
- `ekartoteka_password`
- `enea_password`
- `przedszkole_password`
- `gmail_password`
- `nju_<NUMER_TELEFONU>_password` (dla każdego konta Nju zdefiniowanego w konfiguracji)

Compose już zawiera przykładowe wpisy w sekcji `secrets:` oraz ich podpięcie w `services.findog.secrets`.


## Konfiguracja
Konfiguracja odbywa się przez YAML (plik) + sekrety Dockera + zmienne środowiskowe.

- Ścieżka do pliku konfiguracyjnego: zmienna `CONFIG_PATH` (domyślnie `/config/config.yaml`).
- Dane oraz logi: `DATA_DIR` (domyślnie `/data`).
- Dla deweloperki można nadpisać klucz Dropbox przez ENV: ustaw `ALLOW_ENV_DROPBOX=1` oraz `DROPBOX_API_KEY=...`.

Przykład (fragment) `config/config.yaml`:

```yaml
excel_local_path: "/data/Oplaty.xlsm"
excel_dropbox_path: "/Oplaty.xlsm"

monitored_sheets:
  "Ania & Mario": ["C","I","O","R","U","X","AD","AG","AJ","AM","AP"]
  "Mama": ["C","I"]

# loginy (hasła dostarczane przez Docker secrets)
ekartoteka:   { username: "user@server.com" }
enea:         { username: "user@server.com" }
przedszkole:  { kindergarten: "p_city", username: "rodzic_123456" }

# mapowanie, gdzie w Excelu aktualizować wartości
ekartoteka_sheet: ["Ania & Mario", "Mieszkanie czynsz"]
przedszkole_sheet: ["Ania & Mario", "Placówka Mati"]
enea_sheet:        ["Ania & Mario", "Prąd Enea"]

# powiadomienia mailowe
gmail_user: "noreply@server.com"
recipients: ["u1@server.com","u2@server.com"]

# wiele kont Nju
nju_credentials:
  - { phone: "601200300", sheet: "Greg",   cat: "Telefon a" }
  - { phone: "602200300", sheet: "Joanna", cat: "Telefon b" }
```

Wartości z YAML można nadpisywać per‑klucz przez zmienne środowiskowe Pydantic, np.:
`E_KARTOTEKA__USERNAME=inna_nazwa`.


## Uruchamianie (CLI)
Aplikacja korzysta z Click i pozwala włączać poszczególne etapy/integacje.

Najczęstsze tryby:
- `--enable-all` — pełny przebieg: Dropbox + API + powiadomienia + analytics.
- `--enable-dropbox` — praca na pliku Excel (pobierz → przetwórz → zapisz → wyślij do Dropbox).
- `--enable-notification` — Pushover + e‑mail.
- `--enable-analytics` — wygeneruj wykresy/HTML podsumowania.
- `--enable-api-all` lub `--enable-api <nazwa>` — włącz wszystkie lub wybrane integracje (`ekartoteka`, `iprzedszkole`, `enea`, `nju`).
- `--disable-commit` — nie odsyłaj pliku z powrotem do Dropbox (zapis tylko lokalny).

Przykłady:

```bash
# Pełny przebieg (również domyślne w docker-compose)
python main.py --enable-all

# Tylko integracje + logi, bez dotykania Excela
python main.py --enable-api-all --enable-notification

# Debug/deweloperka: działaj lokalnie na pliku i nie commituj do Dropbox
python main.py --enable-dropbox --disable-commit
```


## Architektura (w skrócie)
- Wzorzec „Chain of Responsibility” — moduły jako Handlery:
  - `FileDownloadHandler` → `FileProcessHandler` → integracje (`eKartoteka`, `Enea`, `iPrzedszkole`, `nju`) → `NotifyOngoingHandler` → `MailingHandler` → `AnalyticsHandler` → `SaveFileLocallyHandler` → `FileCommitHandler`.
- Centralny kontekst (`HandlerContext`) trzyma klienów (Dropbox, Pushover), skonfigurowane ścieżki i `PaymentBook`.
- `PaymentBook` mapuje skoroszyt na kategorie i płatności w bieżącym miesiącu, aktualizuje wartości w odpowiednich kolumnach.

Logi znajdziesz w `DATA_DIR/logs/findog.log`. Dodatkowe artefakty:
- `/data/output.png` (Analytics),
- `/data/output_mail.html` (podgląd e‑maila, gdy wysyłka jest wyłączona).


## Uruchomienie lokalne (bez Dockera)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export CONFIG_PATH="$PWD/config/config.yaml"
export DATA_DIR="$PWD/data"
# (opcjonalnie podczas dev)
export ALLOW_ENV_DROPBOX=1
export DROPBOX_API_KEY="..."
python main.py --enable-all
```

Uwaga: loginy/hasła najlepiej wstrzykiwać jako sekrety Dockera. W trybie lokalnym niektóre hasła trzeba wpisać w plikach w `secrets/` lub dodać własną obsługę ENV.


## Zrzuty ekranu
- Podgląd wiadomości e‑mail: plik HTML generowany przez moduł poczty (jeśli włączony i w trybie podglądu) zapisywany jest jako `/data/output_mail.html`.
- Wykres bieżącego miesiąca: `/data/output.png` po uruchomieniu z flagą `--enable-analytics`.

Wskazówka: do wygenerowania artefaktów lokalnie bez odsyłania pliku do Dropbox możesz użyć np.:

```bash
python main.py --enable-dropbox --enable-api-all --enable-analytics --disable-commit
```

Logo projektu: 

![Findog Logo](templates/findog_logo.png)


## Terminologia
- „eKartoteka” — moduł i usługa do obsługi czynszu/HOA (w kodzie: `EkartotekaHandler`).
- „iPrzedszkole” — integracja z systemem iPrzedszkole.
- „nju” — integracja z nju (rachunki za telefon).
- „Analytics” — prosty moduł generowania wykresów PNG.


## Dobre praktyki i bezpieczeństwo
- Nie commituj żadnych danych w katalogu `secrets/` (repo zawiera `.gitignore`).
- Przechowuj hasła jako Docker secrets. Nigdy nie zapisuj ich w YAML/README.
- Uruchamiaj z minimalnym zakresem uprawnień klucza Dropbox.
- Dbaj o wersjonowanie pliku Excel (kopie w Dropbox).


## Rozwój
- Styl/logowanie: `loguru`.
- Format/analiza: w repo jest workflow Pylint (GitHub Actions).
- Testy: dostępne proste testy jednostkowe dla handlerów (`tests/`). Do uruchomienia lokalnie wymagany `pytest` (nie jest w `requirements.txt`).

```bash
pip install pytest
pytest -q
```

---
Masz pytania lub chcesz rozbudować README (np. o zrzuty ekranu, przykład skoroszytu)? Otwórz issue lub PR.
