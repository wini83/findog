import string
from typing import List

from openpyxl import Workbook
from openpyxl import load_workbook
from payment_sheet import PaymentSheet
from io import BytesIO

import config

from typing import List


class PaymentBook:
    _payment_sheets: List[PaymentSheet] = None
    _workbook: Workbook = None
    _monitored_sheets: List[str] = None

    def __init__(self, monitored_sheets: List[str]):
        self._payment_sheets = []
        self._monitored_sheets = monitored_sheets

    def load_from_file(self, file: bytes):
        self._workbook = load_workbook(filename=BytesIO(file))
        for sheet_name in self.monitored_sheets:
            if self._workbook.__contains__(sheet_name):
                payment_sheet = PaymentSheet(self._workbook[sheet_name], sheet_name, config.active_categories)
                payment_sheet.populate_categories()
                self._payment_sheets.append(payment_sheet)

    @property
    def sheets(self):
        return self._payment_sheets

    @property
    def monitored_sheets(self) -> List[str]:
        return self._monitored_sheets

    @monitored_sheets.setter
    def monitored_sheets(self, value: List[str]):
        self._monitored_sheets = value
