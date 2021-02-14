from payment import Payment


class PaymentCategory:
    name: str = None
    payments: list[Payment] = None

    def __init__(self, name="", column="C"):
        self.name = name
        self.payments = [Payment]
        self.column = column

    def __str__(self):
        return f"{self.name}"
