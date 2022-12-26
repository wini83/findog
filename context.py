from typing import Any, List

from dropbox_client import DropboxClient
from payment_book import PaymentBook
from pushover import Pushover
import config
import os


class HandlerContext:
    dropbox_client: DropboxClient
    payment_book: PaymentBook
    file_object: bytes
    pushover: Pushover
    excel_file_path: str
    ekartoteka_credentials: Any
    ekartoteka_sheet: Any
    enea_credentials: Any
    silent: bool
    recipients: List[str]
    gmail_user: str
    gmail_pass: str
    statuses: List[str]

    def __init__(self, silent: bool = False):
        self.dropbox_client = DropboxClient(config.api_key)
        self.pushover = Pushover(config.pushover_apikey, config.pushover_user)
        self.payment_book = PaymentBook(config.monitored_sheets)
        self.excel_file_path = config.excel_file_path
        self.ekartoteka_credentials = config.ekartoteka
        self.iprzedszkole_credentials = config.przedszkole
        self.ekartoteka_sheet = config.ekartoteka_sheet
        self.enea_credentials = config.enea
        self.iprzedszkole_sheet = config.przedszkole_sheet
        self.enea_sheet = config.enea_sheet
        self.silent = silent
        self.recipients = config.recipients
        self.gmail_user = config.gmail_user
        self.gmail_pass = config.gmail_pass
        self.statuses = []

    @property
    def excel_file_name(self):
        return os.path.basename(self.excel_file_path)
