from typing import List

from Client import Client
from gmail_adapter import GmailAdapter
from messages import DailyMessage
from payment_book import PaymentBook
import payment_book as pb
from loguru import logger

from payment_list_item import PaymentListItem


class Mailer(Client):
    adapter: GmailAdapter = None
    book: PaymentBook = None

    def __init__(self, user: str, password: str, payment_book: PaymentBook, adapter: GmailAdapter = None):
        if adapter is None:
            self.adapter = GmailAdapter(
                host='smtp.gmail.com',
                port=465,
                username=user,
                password=password)
        else:
            self.adapter = adapter
        self.book = payment_book

    def login(self):
        if self.adapter is not None:
            self.adapter.login()
        else:
            raise NotImplementedError()

    def render(self) -> str:
        report = DailyMessage()
        data = self.book.payment_list
        data = pb.sort_payment_list_by_date(data)
        sum_total = sum(payment_li.payment.amount for payment_li in data)
        logger.info(f'Sum total: {sum_total} zł')
        data2: List[PaymentListItem] = []
        for pmt in data:
            if not pmt.payment.paid:
                data2.append(pmt)
        sum_unpaid = sum(payment_li.payment.amount for payment_li in data2)
        logger.info(f'Sum unpaid: {sum_unpaid} zł')
        data_json = pb.make_json_payments(data2)
        return report.render(data=data_json, sum_total=sum_total, sum_unpaid=sum_unpaid)

    def send(self, recipient_email: str, content: str):
        if self.adapter is not None:
            self.adapter.send_mail(recipient_email=recipient_email,
                                   subject="Findog Daily Report",
                                   content=content)
