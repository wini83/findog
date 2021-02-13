import datetime


class Payment:
    amount: float

    def __init__(self, payed=False, due_date=datetime.date(2021, 2, 28), amount=0.0, excel_row=0):
        self.due_date = due_date
        self.amount = amount
        self.payed = payed
        self.excel_row = excel_row

    def __str__(self):
        return f"{self.amount}zł - {self.payed} - {self.due_date}"

    @property
    def payable_within_2days(self) -> bool:
        today = datetime.datetime.now()
        delta = self.due_date - today
        if not self.payed:
            if delta.days <= 2:
                return True
            return False
        else:
            return False
