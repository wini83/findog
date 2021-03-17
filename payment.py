import datetime


class Payment:
    amount: float
    paid: bool
    excel_row: int
    due_date: datetime.date

    def __init__(self, paid=False, due_date=datetime.date(2021, 2, 28), amount=0.0, excel_row=0):
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
        today = datetime.datetime.now()
        delta = self.due_date - today
        if not self.paid:
            if delta.days <= 2:
                return True
            return False
        else:
            return False
