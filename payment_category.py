from payment import Payment
from typing import Dict


class PaymentCategory:
    name: str = None
    payments: Dict[str, Payment] = None
    icon = None

    def __init__(self, name="", column="C"):
        self.name = name
        self.payments = {}
        self.column = column

    def __str__(self):
        return f"{self.name}"

