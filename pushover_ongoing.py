from Client import Client
from payment_book import PaymentBook
from payment_list_item import PaymentListItem
from pushover import Pushover
import os


class PushoverNotifier(Client):
    def login(self):
        pass

    pushover: Pushover
    payment_book: PaymentBook

    def __init__(self, apikey: str, user: str, payment_book):
        self.pushover = Pushover(apikey, user)
        self.payment_book = payment_book

    def notify(self, message: str):
        self.pushover.notify(message)

    def notify_ongoing_payments(self, rundry=False):
        pmt_list: list[PaymentListItem] = self.payment_book.payment_list
        payload: str = ""
        for item in pmt_list:
            if item.payment.payable_within_2days:
                new_str = item.__str__() + os.linesep
                payload += new_str
        if not rundry:
            self.notify(payload)
        return payload
