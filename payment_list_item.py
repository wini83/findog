from payment_sheet import PaymentSheet
from payment_category import PaymentCategory
from payment import Payment


class PaymentListItem:
    _payment: Payment = None
    _category: PaymentCategory = None
    _sheet: PaymentSheet = None

    def __init__(self, payment: Payment, category: PaymentCategory, sheet: PaymentSheet):
        self._payment = payment
        self._category = category
        self._sheet = sheet

    @property
    def payment(self) -> Payment:
        return self._payment

    @property
    def category(self) -> PaymentCategory:
        return self._category

    @property
    def sheet(self) -> PaymentSheet:
        return self._sheet

    def to_dict(self):
        return {'sheet': self._sheet.name, 'category': self._category.name,
                'amount': self._payment.amount.__round__(2), 'paid': self._payment.paid,
                'duedate': self._payment.due_date.strftime("%Y-%m-%d")}

    def __str__(self):
        result: str = ""
        if self.sheet is not None:
            result += self._sheet.name
        if self.category is not None:
            result = f'{result} >> {self._category.name}'
        if self._payment is not None:
            result = f'{result} >> {self._payment}'
        return result
