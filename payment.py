"""Payment model and related helpers."""

from datetime import datetime

import numpy as np


class Payment:
    """Represents a single payment entry with due date and status."""

    amount: float
    paid: bool
    excel_row: int
    due_date: datetime

    def __init__(self, paid=False, due_date=datetime.now(), amount=0.0, excel_row=0):
        """Create a payment with defaults for status, date, amount and row."""
        self.due_date = due_date
        self.amount: float = amount
        self.paid: bool = paid
        self.excel_row: int = excel_row

    def __str__(self):
        """Return a human-readable description of the payment."""
        return f"{self.amount:.2f}zł - {self.paid_status} - {self.due_date:%Y-%m-%d}"

    @property
    def paid_status(self):
        """Text label describing whether the payment is paid."""
        if self.paid:
            return "paid"
        else:
            return "not yet paid"

    @property
    def payable_within_2days(self) -> bool:
        """True if unpaid and due date is within the next two days."""
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
        """True if past due and still unpaid."""
        today = datetime.now()
        delta = self.due_date - today
        if delta.total_seconds() < 0 and not self.paid:
            return True
        else:
            return False

    @property
    def b_days_left(self) -> int:
        """Business days left until due date."""
        today = datetime.now()
        return int(np.busday_count(f'{today:%Y-%m-%d}', f'{self.due_date:%Y-%m-%d}'))
