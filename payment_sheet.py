from typing import Any

import string
from datetime import datetime

from openpyxl.worksheet.worksheet import Worksheet

from payment import Payment
from payment_category import PaymentCategory

from typing import List


class PaymentSheet:
    _sheet: Worksheet = None
    _name: string = None
    _categories: List[PaymentCategory] = None
    _monitored_cols: List[str] = None

    def __init__(self, worksheet: Worksheet, name: string, monitored_cols: List[str]):
        self._categories = []
        self._sheet = worksheet
        self._name = name
        self._monitored_cols = monitored_cols

    @property
    def monitored_cols(self) -> List[str]:
        return self._monitored_cols

    @monitored_cols.setter
    def monitored_cols(self, value: List[str]):
        self._monitored_cols = value

    @property
    def categories(self) -> List[PaymentCategory]:
        return self._categories

    @property
    def sheet(self) -> Worksheet:
        return self._sheet

    @property
    def name(self):
        return self._name

    @property
    def get_active_row(self) -> int:
        current_month = datetime.now().month
        current_year = datetime.now().year
        current_row = 2
        while self._sheet[f"A{current_row}"].value is not None:
            date_item = self._sheet[f"A{current_row}"].value
            if (date_item.month == current_month) and (date_item.year == current_year):
                break
            current_row += 1
        return current_row

    def populate_categories(self):
        active_row = self.get_active_row
        for column in self._monitored_cols:
            name = self._sheet[f"{column}1"].value
            item: PaymentCategory = PaymentCategory(name=name, column=column)
            amount = float(self._sheet[f"{column}{active_row}"].value)
            column_int = self._sheet[f"{column}{active_row}"].col_idx
            try:
                done = bool(self._sheet.cell(column=column_int + 1, row=active_row).value)
            except ValueError:
                done = False

            due_date = self._sheet.cell(column=column_int + 2, row=active_row).value
            new_payment = Payment(paid=done, due_date=due_date, amount=amount, excel_row=active_row)
            item.payments.append(new_payment)

            self._categories.append(item)
