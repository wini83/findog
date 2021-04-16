from typing import Any

from dropbox_client import DropboxClient
from payment_book import PaymentBook
from pushover import Pushover
import config


class HandlerContext:
    dropbox_client: DropboxClient
    payment_book: PaymentBook
    file_object: bytes
    pushover: Pushover
    excel_file_path: str
    ekartoteka_creditentials: Any
    ekartoteka_sheet: Any
    silent: bool
    recipient_email: str
    gmail_user: str
    gmail_pass: str

    def __init__(self, silent: bool = False):
        self.dropbox_client = DropboxClient(config.api_key)
        self.pushover = Pushover(config.pushover_apikey, config.pushover_user)
        self.payment_book = PaymentBook(config.monitored_sheets)
        self.excel_file_path = config.excel_file_path
        self.ekartoteka_creditentials = config.ekartoteka
        self.ekartoteka_sheet = config.ekartoteka_sheet
        self.silent = silent
        self.recipient_email = config.recipient_email
        self.gmail_user = config.gmail_user
        self.gmail_pass = config.gmail_pass
