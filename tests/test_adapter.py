from datetime import datetime
from io import BytesIO

from openpyxl import Workbook

from findog_legacy_adapter import LegacyWorkbookAdapter, load_payment_book


def _workbook_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Home"
    sheet.append(["Date", "Sum", "Rent", None, None])
    now = datetime.now()
    sheet.append([datetime(now.year, now.month, 1), 0, 1500.0, 0, now])
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def test_load_payment_book_returns_legacy_domain_objects():
    payment_book = load_payment_book(_workbook_bytes(), {"Home": ["C"]})

    assert len(payment_book.payment_list) == 1
    assert payment_book.payment_list[0].payment.amount == 1500.0


def test_adapter_downloads_before_loading():
    class Downloader:
        def __init__(self):
            self.path: str | None = None

        def retrieve_file(self, file_path: str) -> bytes:
            self.path = file_path
            return _workbook_bytes()

    downloader = Downloader()
    payment_book = LegacyWorkbookAdapter({"Home": ["C"]}).download_and_load(
        downloader, "/Oplaty.xlsm"
    )

    assert downloader.path == "/Oplaty.xlsm"
    assert len(payment_book.payment_list) == 1
