"""Load legacy Findog workbooks for consumption by another application."""

from collections.abc import Mapping, Sequence
from typing import Protocol

from .dropbox import DropboxClient
from .payment_book import PaymentBook


class WorkbookDownloader(Protocol):
    """Minimal interface required to retrieve a legacy workbook."""

    def retrieve_file(self, file_path: str) -> bytes:
        """Return the remote workbook contents."""


class LegacyWorkbookAdapter:
    """Convert an Excel workbook into the existing Findog domain objects."""

    def __init__(
        self,
        monitored_sheets: Mapping[str, Sequence[str]],
        interpret_codes: bool = False,
    ):
        self._monitored_sheets = {
            sheet_name: list(columns)
            for sheet_name, columns in monitored_sheets.items()
        }
        self._interpret_codes = interpret_codes

    def load_bytes(self, workbook_bytes: bytes) -> PaymentBook:
        """Parse XLSX/XLSM bytes and return a populated :class:`PaymentBook`."""
        payment_book = PaymentBook(
            self._monitored_sheets, interpret_codes=self._interpret_codes
        )
        payment_book.load_and_process(workbook_bytes)
        return payment_book

    def download_and_load(
        self, downloader: WorkbookDownloader, dropbox_path: str
    ) -> PaymentBook:
        """Download one workbook and parse it into legacy payment objects."""
        return self.load_bytes(downloader.retrieve_file(dropbox_path))


def load_payment_book(
    workbook_bytes: bytes,
    monitored_sheets: Mapping[str, Sequence[str]],
    interpret_codes: bool = False,
) -> PaymentBook:
    """Parse workbook bytes into a populated :class:`PaymentBook`."""
    return LegacyWorkbookAdapter(
        monitored_sheets, interpret_codes=interpret_codes
    ).load_bytes(workbook_bytes)


def load_payment_book_from_dropbox(
    access_token: str,
    dropbox_path: str,
    monitored_sheets: Mapping[str, Sequence[str]],
    interpret_codes: bool = False,
) -> PaymentBook:
    """Download a Dropbox workbook and parse it into a :class:`PaymentBook`."""
    adapter = LegacyWorkbookAdapter(monitored_sheets, interpret_codes=interpret_codes)
    return adapter.download_and_load(DropboxClient(access_token), dropbox_path)
