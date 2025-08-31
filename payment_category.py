"""Category grouping payments within a sheet."""

from typing import Dict

from payment import Payment


class PaymentCategory:
    """Represents a category column in the workbook."""

    name: str = None
    payments: Dict[str, Payment] = None
    icon = None

    def __init__(self, name="", column="C"):
        """Create a category with a name and assigned column letter."""
        self.name = name
        self.payments = {}
        self.column = column

    def __str__(self):
        """Return the category name for display."""
        return f"{self.name}"
