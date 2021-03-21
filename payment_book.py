import string
from datetime import date
from io import BytesIO
from typing import List

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Color

from payment_sheet import PaymentSheet


class PaymentBook:
    _payment_sheets: List[PaymentSheet] = None
    _workbook: Workbook = None
    _monitored_sheets = None

    def __init__(self, monitored_sheets):
        self._payment_sheets = []
        self._monitored_sheets = monitored_sheets

    def load_from_file(self, file: bytes):
        self._workbook = load_workbook(filename=BytesIO(file), keep_vba=True)
        for sheet_name, monit_cats in self.monitored_sheets.items():
            if self._workbook.__contains__(sheet_name):
                payment_sheet = PaymentSheet(self._workbook[sheet_name], sheet_name, monit_cats)
                payment_sheet.populate_categories()
                self._payment_sheets.append(payment_sheet)

    def save_to_file(self, filename):
        self._workbook.save(filename=filename)

    def update_current_payment_amount(self, sheet_name: string, category_name: string, amount: float):
        for sheet in self._payment_sheets:
            if sheet.name == sheet_name:
                for cat in sheet.categories:
                    if cat.name == category_name:
                        for pmt in cat.payments:
                            if pmt.due_date.year == date.today().year and pmt.due_date.month == date.today().month:
                                pmt.amount = amount
                                cell_local = f'{cat.column}{pmt.excel_row}'
                                sheet.sheet[cell_local] = amount
                                # sheet.sheet[cell_local].fill = PatternFill(bgColor=Color(indexed=5),
                                # fill_type="solid")
                                break
                        break
                break

    @property
    def sheets(self):
        return self._payment_sheets

    @property
    def monitored_sheets(self):
        return self._monitored_sheets

    @monitored_sheets.setter
    def monitored_sheets(self, value):
        self._monitored_sheets = value
