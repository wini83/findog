import string
import calendar
from datetime import datetime, timedelta

from openpyxl.cell import Cell
from openpyxl.styles import PatternFill, Color
from openpyxl.worksheet.worksheet import Worksheet

from payment import Payment
from payment_category import PaymentCategory

from typing import List

RED_FILL = PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
GREEN_FILL = PatternFill(fill_type='solid', start_color="00FF00")
YELLOW_FILL = PatternFill(fill_type='solid', start_color=Color(indexed=5))
BLUE_FILL = PatternFill(fill_type='solid', start_color="6ED1FE")


def add_months(sourcedate: datetime, months: int):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)


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

    def populate_categories(self, active_row: int):
        for column in self._monitored_cols:
            name = self._sheet[f"{column}1"].value
            item: PaymentCategory = PaymentCategory(name=name, column=column)
            amount = float(self._sheet[f"{column}{active_row}"].value)
            column_int = self._sheet[f"{column}{active_row}"].col_idx
            try:
                paid = bool(self._sheet.cell(column=column_int + 1, row=active_row).value)
            except ValueError:
                paid = False

            due_date = self._sheet.cell(column=column_int + 2, row=active_row).value
            new_payment = Payment(paid=paid, due_date=due_date, amount=amount, excel_row=active_row)
            item.payments.append(new_payment)

            self._categories.append(item)
            self.format_payment(column_int, new_payment)

    # noinspection PyDunderSlots,PyUnresolvedReferences
    def format_payment(self, column: int, payment: Payment):
        # TODO: add some checks
        cell_amount: Cell = self.sheet.cell(row=payment.excel_row, column=column)
        cell_paid: Cell = self.sheet.cell(row=payment.excel_row, column=column + 1)
        cell_due_date: Cell = self.sheet.cell(row=payment.excel_row, column=column + 2)
        if payment.overdue:
            cell_amount.fill = RED_FILL
            cell_paid.fill = RED_FILL
            cell_due_date.fill = RED_FILL
        elif payment.paid:
            cell_amount.fill = GREEN_FILL
            cell_paid.fill = GREEN_FILL
            cell_due_date.fill = GREEN_FILL
        elif payment.due_date.year == datetime.now().year and payment.due_date.month == datetime.now().month:
            cell_amount.fill = YELLOW_FILL
            cell_paid.fill = YELLOW_FILL
            cell_due_date.fill = YELLOW_FILL
        else:
            cell_amount.fill = BLUE_FILL
            cell_paid.fill = BLUE_FILL
            cell_due_date.fill = BLUE_FILL

    def populate_next_month(self, current_row: int):
        # TODO:add some logic

        proceed_further = self._process_next_month_cell(current_row)
        if proceed_further:
            self._process_next_sum(current_row)
            self._populate_next_month_payments(current_row)

    # noinspection PyDunderSlots,PyUnresolvedReferences
    def _populate_next_month_payments(self, current_row: int):
        for category in self.categories:
            current_amount_cell: Cell = self.sheet[f'{category.column}{current_row}']
            current_duedate_cell = self.sheet.cell(row=current_row, column=current_amount_cell.col_idx + 2)

            next_amount_cell: Cell = self.sheet[f'{category.column}{current_row + 1}']
            next_paid_cell = self.sheet.cell(row=current_row + 1, column=current_amount_cell.col_idx + 1)
            next_duedate_cell = self.sheet.cell(row=current_row + 1, column=current_amount_cell.col_idx + 2)
            if next_amount_cell.value is None:
                next_amount_cell.value = current_amount_cell.value
            next_amount_cell.fill = BLUE_FILL

            if next_paid_cell.value is None:
                next_paid_cell.value = 0
            next_paid_cell.fill = BLUE_FILL

            if next_duedate_cell.value is None:
                next_duedate_cell.value = add_months(current_duedate_cell.value, 1)
            next_duedate_cell.fill = BLUE_FILL
        pass

    def _process_next_sum(self, current_row):
        cell_this_month_sum: Cell = self.sheet.cell(column=2, row=current_row)
        cell_next_month_sum: Cell = self.sheet.cell(column=2, row=current_row + 1)
        print(f'{cell_this_month_sum.value} - {cell_next_month_sum}')

    # noinspection PyDunderSlots,PyUnresolvedReferences
    def _process_next_month_cell(self, current_row):
        cell_next_month: Cell = self.sheet.cell(column=1, row=current_row + 1)
        now = datetime.now()
        now = datetime(year=now.year, month=now.month, day=now.day)
        next_month_date = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        if cell_next_month.value is None:
            cell_next_month.value = next_month_date
            cell_next_month.style = self.sheet.cell(column=1, row=current_row).style
            cell_next_month.fill = BLUE_FILL
            process = True
        elif cell_next_month.value == next_month_date:
            cell_next_month.fill = BLUE_FILL
            process = True
        else:
            print(f'{self.name} - {cell_next_month.value} ')
            process = False
        return process
