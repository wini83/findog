

import importlib
import os
from pathlib import Path
from typing import List, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret(path: str) -> Optional[str]:
    p = Path(path)
    return p.read_text(encoding="utf-8").strip() if p.exists() else None

class Cred(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    kindergarten: Optional[str] = None        # dla przedszkole
    phone: Optional[str] = None
    phone: Optional[str] = None
    sheet: Optional[str] = None
    cat: Optional[str] = None
    # dla nju

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    # proste pola
    dropbox_apikey: Optional[str] = None

    excel_dropbox_path: str = "/Oplaty.xlsm"      # ŚCIEŻKA W DROPBOX!
    excel_local_path: Path = Path("/data/Oplaty.xlsm")  # ŚCIEŻKA LOKALNA

    gmail_user: str = "user@example.com"
    gmail_pass: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)

    # słowniki/listy
    monitored_sheets: Dict[str, List[str]] = Field(default_factory=dict)
    ekartoteka_sheet: List[str] = Field(default_factory=list)
    przedszkole_sheet: List[str] = Field(default_factory=list)
    enea_sheet: List[str] = Field(default_factory=list)

    # serwisy
    ekartoteka: Cred = Cred()
    enea: Cred = Cred()
    przedszkole: Cred = Cred()

    # pushover
    pushover_apikey: Optional[str] = None
    pushover_user: Optional[str] = None

    # nju: lista kont
    nju_credentials: List[Cred] = Field(default_factory=list)

    @classmethod
    def from_all(cls) -> "Settings":
        cfg_path = Path(os.getenv("CONFIG_PATH", "/config/config.yaml"))
        data = {}
        if cfg_path.exists():
            with cfg_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        s = cls(**data)  # 2) ENV nadpisuje (pydantic-settings to robi automatycznie)

        # 3) Docker secrets → /run/secrets/...
        secret = _read_secret("/run/secrets/dropbox_apikey")              # Docker secret
        env_dev = os.getenv("DROPBOX_API_KEY") if os.getenv("ALLOW_ENV_DROPBOX") == "1" else None
        s.dropbox_apikey = secret or env_dev or s.dropbox_apikey

        s.pushover_apikey = s.pushover_apikey or _read_secret("/run/secrets/pushover_apikey")
        s.pushover_user   = s.pushover_user   or _read_secret("/run/secrets/pushover_user")
        s.gmail_pass      = s.gmail_pass      or _read_secret("/run/secrets/gmail_password")


        # ekartoteka / enea / przedszkole (same hasła)
        if not s.ekartoteka.password:
            s.ekartoteka.password = _read_secret("/run/secrets/ekartoteka_password")
        if not s.enea.password:
            s.enea.password = _read_secret("/run/secrets/enea_password")
        if not s.przedszkole.password:
            s.przedszkole.password = _read_secret("/run/secrets/przedszkole_password")

        # nju: dopasuj po phone → /run/secrets/nju_<phone>_password
        for cred in s.nju_credentials:
            if cred.phone and not cred.password:
                cred.password = _read_secret(f"/run/secrets/nju_{cred.phone}_password")

        # Walidacje lekkie
        if not s.dropbox_apikey:
            raise ValueError("Brak api_key (ustaw w config.yaml lub ENV)")
        if not s.gmail_user:
            raise ValueError("Brak gmail_user")
        return s

settings = Settings.from_all()
