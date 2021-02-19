import string
from typing import List

from openpyxl import Workbook
from openpyxl import load_workbook
from payment_sheet import PaymentSheet
from io import BytesIO

from typing import List


class PaymentBook:
    _payment_sheets: List[PaymentSheet] = None
    _workbook: Workbook = None
    _monitored_sheets = None

    def __init__(self, monitored_sheets):
        self._payment_sheets = []
        self._monitored_sheets = monitored_sheets

    def load_from_file(self, file: bytes):
        self._workbook = load_workbook(filename=BytesIO(file))
        for sheet_name, monit_cats in self.monitored_sheets.items():
            if self._workbook.__contains__(sheet_name):
                payment_sheet = PaymentSheet(self._workbook[sheet_name], sheet_name, monit_cats)
                payment_sheet.populate_categories()
                self._payment_sheets.append(payment_sheet)

    @property
    def sheets(self):
        return self._payment_sheets

    @property
    def monitored_sheets(self):
        return self._monitored_sheets

    @monitored_sheets.setter
    def monitored_sheets(self, value):
        self._monitored_sheets = value
