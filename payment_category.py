from payment import Payment
from typing import List


class PaymentCategory:
    name: str = None
    payments: List[Payment] = None

    def __init__(self, name="", column="C"):
        self.name = name
        self.payments = []
        self.column = column

    def __str__(self):
        return f"{self.name}"
