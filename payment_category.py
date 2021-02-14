from payment import Payment


class PaymentCategory:
    name: str = None

    def __init__(self, name="", column="C"):
        self.name = name
        self.payments = list[Payment]
        self.column = column

    def __str__(self):
        return f"{self.name}"
