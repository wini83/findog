import string
from datetime import date, datetime
from io import BytesIO
from typing import Dict

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.cell import Cell

from payment_sheet import PaymentSheet


class PaymentBook:
    _payment_sheets: Dict[str, PaymentSheet] = None
    _workbook: Workbook = None
    _monitored_sheets = None

    def __init__(self, monitored_sheets):
        self._payment_sheets = {}
        self._monitored_sheets = monitored_sheets

    def load_and_process(self, file: bytes):
        self._workbook = load_workbook(filename=BytesIO(file), keep_vba=True)
        for sheet_name, monit_cats in self.monitored_sheets.items():
            if self._workbook.__contains__(sheet_name):
                payment_sheet = PaymentSheet(self._workbook[sheet_name], sheet_name, monit_cats)
                current_row = payment_sheet.get_active_row
                if current_row > 1:
                    payment_sheet.populate_categories(current_row)
                    payment_sheet.populate_next_month(current_row)
                self._payment_sheets[sheet_name] = payment_sheet

    def save_to_file(self, filename):
        self._workbook.save(filename=filename)

    def update_current_payment(self, sheet_name: string, category_name: string,
                               amount: float = None,
                               paid: bool = None,
                               due_date: datetime = None):
        # TODO: refactor
        sheet: PaymentSheet = self._payment_sheets[sheet_name]
        if sheet.name == sheet_name:
            cat = sheet.categories[category_name]
            # TODO:Secure
            if cat.name == category_name:
                now = datetime.now()
                pmt = cat.payments[f'{now.year}-{now.month}']
                # TODO:Secure
                if pmt.due_date.year == date.today().year and pmt.due_date.month == date.today().month:
                    cell_amount: Cell = sheet.sheet[f'{cat.column}{pmt.excel_row}']
                    cell_paid: Cell = sheet.sheet.cell(row=cell_amount.row, column=cell_amount.column + 1)
                    cell_due_date: Cell = sheet.sheet.cell(row=cell_amount.row,
                                                           column=cell_amount.column + 2)
                    if amount is not None:
                        pmt.amount = amount
                        cell_amount.value = amount
                    if paid is not None:
                        pmt.paid = paid
                        cell_paid.value = int(paid)
                    if due_date is not None:
                        pmt.due_date = due_date
                        cell_due_date.value = due_date
                        sheet.format_payment(cell_amount.column, pmt)


    @property
    def sheets(self):
        return self._payment_sheets

    @property
    def monitored_sheets(self):
        return self._monitored_sheets

    @monitored_sheets.setter
    def monitored_sheets(self, value):
        self._monitored_sheets = value
