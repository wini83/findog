from datetime import datetime

import numpy as np


class Payment:
    amount: float
    paid: bool
    excel_row: int
    due_date: datetime

    def __init__(self, paid=False, due_date=datetime.now(), amount=0.0, excel_row=0):
        self.due_date = due_date
        self.amount: float = amount
        self.paid: bool = paid
        self.excel_row: int = excel_row

    def __str__(self):
        return f"{self.amount:.2f}zł - {self.paid_status} - {self.due_date:%Y-%m-%d}"

    @property
    def paid_status(self):
        if self.paid:
            return "paid"
        else:
            return "not yet paid"

    @property
    def payable_within_2days(self) -> bool:
        today = datetime.now()
        delta = self.due_date - today
        if not self.paid:
            if delta.days <= 2:
                return True
            return False
        else:
            return False

    @property
    def overdue(self) -> bool:
        today = datetime.now()
        delta = self.due_date - today
        if delta.total_seconds() < 0 and not self.paid:
            return True
        else:
            return False

    @property
    def b_days_left(self) -> int:
        today = datetime.now()
        return int(np.busday_count(f'{today:%Y-%m-%d}', f'{self.due_date:%Y-%m-%d}'))