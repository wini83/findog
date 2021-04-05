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
    def payment(self):
        return self.payment

    @property
    def category(self):
        return self.category

    def sheet(self):
        return self._sheet
