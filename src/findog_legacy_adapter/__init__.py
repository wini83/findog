"""Adapter exposing Findog's legacy Excel data as Python objects."""

from .adapter import (
    LegacyWorkbookAdapter,
    load_payment_book,
    load_payment_book_from_dropbox,
)
from .payment_book import PaymentBook

__all__ = [
    "LegacyWorkbookAdapter",
    "PaymentBook",
    "load_payment_book",
    "load_payment_book_from_dropbox",
]
