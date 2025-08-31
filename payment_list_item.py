"""Aggregated view of payment with its category and sheet."""

from payment import Payment
from payment_category import PaymentCategory
from payment_sheet import PaymentSheet


class PaymentListItem:
    """DTO-like wrapper combining payment, category and sheet info."""

    _payment: Payment = None
    _category: PaymentCategory = None
    _sheet: PaymentSheet = None

    def __init__(
        self, payment: Payment, category: PaymentCategory, sheet: PaymentSheet
    ):
        """Initialize with related payment, category and sheet."""
        self._payment = payment
        self._category = category
        self._sheet = sheet

    @property
    def payment(self) -> Payment:
        """Return the wrapped payment."""
        return self._payment

    @property
    def category(self) -> PaymentCategory:
        """Return the associated category."""
        return self._category

    @property
    def sheet(self) -> PaymentSheet:
        """Return the source sheet."""
        return self._sheet

    def to_dict(self):
        """Serialize to a dict for JSON rendering in reports."""
        return {
            'sheet': self._sheet.name,
            'category': self._category.name,
            'amount': round(self._payment.amount, 2),
            'paid': self._payment.paid,
            'duedate': self._payment.due_date.strftime("%Y-%m-%d"),
            'b_days_left': self._payment.b_days_left,
            'icon': self._category.icon,
        }

    def __str__(self):
        """Readable breadcrumb-like representation of the list item."""
        result: str = ""
        if self.sheet is not None:
            result += self._sheet.name
        if self.category is not None:
            result = f'{result} >> {self._category.name}'
        if self._payment is not None:
            result = f'{result} >> {self._payment}'
        return result
