"""Adapter exposing Findog's legacy Excel data as Python objects."""

from .adapter import (
    LegacyWorkbookAdapter,
    load_payment_book,
    load_payment_book_from_dropbox,
)
from .payment_book import PaymentBook
from .payment_sheet import PaymentCodeError, interpret_category_code

__all__ = [
    "LegacyWorkbookAdapter",
    "PaymentBook",
    "PaymentCodeError",
    "interpret_category_code",
    "load_payment_book",
    "load_payment_book_from_dropbox",
]
