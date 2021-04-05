from Client import Client
from gmail_adapter import GmailAdapter
from messages import DailyMessage
from payment_book import PaymentBook
import payment_book as pb


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

    def send(self, recipient_email: str):
        report = DailyMessage()
        data = self.book.payment_list
        data = pb.sort_payment_list_by_date(data)
        data2 = []
        for pmt in data:
            if not pmt.payment.paid:
                data2.append(pmt)
        data_json = pb.make_json_payments(data2)

        if self.adapter is not None:
            self.adapter.send_mail(recipient_email=recipient_email,
                                   subject="Findog Daily Report",
                                   content=report.render(data=data_json))
