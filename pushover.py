import http.client
import os
import urllib
from typing import List

from Client import Client
from payment_book import PaymentBook
from payment_list_item import PaymentListItem


class Pushover(Client):
    def __init__(self, apikey: str, user: str):
        self.apikey = apikey
        self.user = user

    def login(self):
        pass

    def notify(self, message: str):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": self.apikey,
                         "user": self.user,
                         "message": message,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()


class PushoverNotifier(Client):
    def login(self):
        pass

    pushover: Pushover
    payment_book: PaymentBook

    def __init__(self, pushover: Pushover, payment_book):
        self.pushover = pushover
        self.payment_book = payment_book

    def notify(self, message: str):
        self.pushover.notify(message)

    def notify_ongoing_payments(self, rundry=False):
        pmt_list: List[PaymentListItem] = self.payment_book.payment_list
        payload: str = ""
        for item in pmt_list:
            if item.payment.payable_within_2days:
                new_str = item.__str__() + os.linesep
                payload += new_str
        if not rundry:
            self.notify(payload)
        return payload
