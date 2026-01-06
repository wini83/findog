"""Category grouping payments within a sheet."""

from payment import Payment


class PaymentCategory:
    """Represents a category column in the workbook."""

    name: str = None
    payments: dict[str, Payment] = None
    icon = None

    def __init__(self, name="", column="C"):
        """Create a category with a name and assigned column letter."""
        self.name = name
        self.payments = {}
        self.column = column

    def __str__(self):
        """Return the category name for display."""
        return f"{self.name}"

    def has_payments(self) -> bool:
        """Return True when the category contains any payments."""
        return bool(self.payments)
