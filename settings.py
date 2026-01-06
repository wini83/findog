import os
from pathlib import Path

import yaml
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Paths & helpers
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SECRETS_DIR = Path(os.getenv("SECRETS_DIR", "/run/secrets"))

logger.info("Using secrets dir: {}", DEFAULT_SECRETS_DIR)

def _read_file(path: Path) -> str | None:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return None


def read_secret(name: str) -> str | None:
    return _read_file(DEFAULT_SECRETS_DIR / name)


def env_if_allowed(name: str, allow_flag: str) -> str | None:
    return os.getenv(name) if os.getenv(allow_flag) == "1" else None


# =============================================================================
# Models
# =============================================================================

class Cred(BaseModel):
    username: str | None = None
    password: str | None = None
    kindergarten: str | None = None
    phone: str | None = None
    sheet: str | None = None
    cat: str | None = None


class Settings(BaseSettings):
    """
    Settings loader order:
    1. YAML (config.yaml)
    2. ENV (pydantic-settings)
    3. Docker secrets (/run/secrets)
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Core paths
    # -------------------------------------------------------------------------

    data_dir: Path = DEFAULT_DATA_DIR
    excel_filename: str = "Oplaty.xlsm"

    # -------------------------------------------------------------------------
    # Dropbox / Excel
    # -------------------------------------------------------------------------

    dropbox_apikey: str | None = None
    excel_dropbox_path: str = "/Oplaty.xlsm"  # ścieżka W DROPBOXIE

    @property
    def excel_local_path(self) -> Path:
        return self.data_dir / self.excel_filename

    # -------------------------------------------------------------------------
    # Mail
    # -------------------------------------------------------------------------

    gmail_user: str = "user@example.com"
    gmail_pass: str | None = None
    recipients: list[str] = Field(default_factory=list)

    # -------------------------------------------------------------------------
    # Sheets / mappings
    # -------------------------------------------------------------------------

    monitored_sheets: dict[str, list[str]] = Field(default_factory=dict)
    ekartoteka_sheet: list[str] = Field(default_factory=list)
    przedszkole_sheet: list[str] = Field(default_factory=list)
    enea_sheet: list[str] = Field(default_factory=list)

    # -------------------------------------------------------------------------
    # Services
    # -------------------------------------------------------------------------

    ekartoteka: Cred = Field(default_factory=Cred)
    enea: Cred = Field(default_factory=Cred)
    przedszkole: Cred = Field(default_factory=Cred)

    # -------------------------------------------------------------------------
    # Pushover
    # -------------------------------------------------------------------------

    pushover_apikey: str | None = None
    pushover_user: str | None = None

    # -------------------------------------------------------------------------
    # NJU (multiple accounts)
    # -------------------------------------------------------------------------

    nju_credentials: list[Cred] = Field(default_factory=list)

    # -------------------------------------------------------------------------
    # Loader
    # -------------------------------------------------------------------------

    @classmethod
    def from_all(cls) -> "Settings":
        # 1️⃣ YAML
        cfg_path = Path(os.getenv("CONFIG_PATH", DEFAULT_CONFIG_PATH))
        data: dict = {}

        if cfg_path.exists():
            with cfg_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        # 2️⃣ ENV (pydantic does this automatically)
        s = cls(**data)

        # 3️⃣ DATA_DIR override (env)
        s.data_dir = Path(os.getenv("DATA_DIR", s.data_dir))

        # ensure data/logs exists
        (s.data_dir / "logs").mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------------
        # Secrets
        # ---------------------------------------------------------------------
        
        s.dropbox_apikey = (
            read_secret("dropbox_apikey")
            or env_if_allowed("DROPBOX_API_KEY", "ALLOW_ENV_DROPBOX")
            or s.dropbox_apikey
        )

        s.pushover_apikey = s.pushover_apikey or read_secret("pushover_apikey")
        s.pushover_user = s.pushover_user or read_secret("pushover_user")
        s.gmail_pass = s.gmail_pass or read_secret("gmail_password")

        if not s.ekartoteka.password:
            s.ekartoteka.password = read_secret("ekartoteka_password")
        if not s.enea.password:
            s.enea.password = read_secret("enea_password")
        if not s.przedszkole.password:
            s.przedszkole.password = read_secret("przedszkole_password")

        for cred in s.nju_credentials:
            if cred.phone and not cred.password:
                cred.password = read_secret(f"nju_{cred.phone}_password")

        # ---------------------------------------------------------------------
        # Light validation (fail fast, but not at import time)
        # ---------------------------------------------------------------------

        if not s.dropbox_apikey:
            raise ValueError("Brak dropbox_apikey (config / ENV / secret)")

        if not s.gmail_user:
            raise ValueError("Brak gmail_user")

        return s
