import os

from typing import List
from api_clients.dropbox_client import DropboxClient
from payment_book import PaymentBook
from pushover import Pushover
from settings import Settings

class HandlerContext:
    def __init__(self, settings: Settings, silent: bool = False):
        self.dropbox_client = DropboxClient(settings.dropbox_apikey)
        self.pushover = Pushover(settings.pushover_apikey, settings.pushover_user)
        self.payment_book = PaymentBook(settings.monitored_sheets)
        self.excel_dropbox_path = settings.excel_dropbox_path
        self.excel_local_path = str(settings.excel_local_path)
        self.ekartoteka_credentials = settings.ekartoteka.model_dump()
        self.iprzedszkole_credentials = settings.przedszkole.model_dump()
        self.ekartoteka_sheet = settings.ekartoteka_sheet
        self.enea_credentials = settings.enea.model_dump()
        self.iprzedszkole_sheet = settings.przedszkole_sheet
        self.enea_sheet = settings.enea_sheet
        self.silent = silent
        self.recipients = settings.recipients
        self.gmail_user = settings.gmail_user
        self.gmail_pass = settings.gmail_pass or ""
        self.statuses: List[str] = []
        self.nju_credentials = [c.model_dump() for c in settings.nju_credentials]
        self.no_excel = False

    @property
    def excel_file_name(self):
        return os.path.basename(self.excel_local_path)
