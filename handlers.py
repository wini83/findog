import os
from abc import ABC, abstractmethod

from context import HandlerContext
from ekartoteka import Ekartoteka
from mailer import Mailer
from payment_list_item import PaymentListItem


class Handler(ABC):
    """
    The Handler interface declares a method for building the chain of handlers.
    It also declares a method for executing a request.
    """

    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def handle(self, context: HandlerContext) -> HandlerContext:
        pass


class AbstractHandler(Handler):
    """
    The default chaining behavior can be implemented inside a base handler
    class.
    """

    _next_handler: Handler = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        # Returning a handler from here will let us link handlers in a
        # convenient way like this:
        # monkey.set_next(squirrel).set_next(dog)
        return handler

    @abstractmethod
    def handle(self, context: HandlerContext) -> HandlerContext:
        if self._next_handler:
            return self._next_handler.handle(context)
        return context


class FileDownloadHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Downloading File...")
        if context is not None:
            if context.dropbox_client is not None and context.excel_file_path is not None:
                context.file_object = context.dropbox_client.retrieve_file(context.excel_file_path)
                print(f"File {context.excel_file_path} downloaded")
        print(f'{"=" * 60}')
        return super().handle(context)


class FileProcessHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Processing Excel File")
        print("Input - Monitored Columns")
        if context.file_object is not None and context.payment_book is not None:
            for name, mk in context.payment_book.monitored_sheets.items():
                print(f'{name} - {mk}')
            context.payment_book.load_and_process(context.file_object)
            print(f"File {context.excel_file_path} processed succesfully")
        print(f'{"=" * 60}')
        return super().handle(context)


class NotifyOngoingHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Notify payments payable in 2 days ")
        pmt_list: list[PaymentListItem] = context.payment_book.payment_list
        payload: str = ""
        i: int = 0
        for item in pmt_list:
            if item.payment.payable_within_2days:
                new_str = item.__str__() + os.linesep
                payload += new_str
                i += 1
        if i > 0:
            context.pushover.notify(payload)
        else:
            payload = "None :)"
        print(payload)
        print(f'{"=" * 60}')
        return super().handle(context)


class EkartotekaHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Ekartoteka")
        ekart = Ekartoteka(context.ekartoteka_creditentials, context.payment_book)
        ekart.login()
        apartment_fee, delta = ekart.update_payment_book(context.ekartoteka_sheet[0], context.ekartoteka_sheet[1])
        ekart_str = f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł'
        print(ekart_str)
        if not context.silent:
            context.pushover.notify(f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł')
        print(f'{"=" * 60}')
        return super().handle(context)


class SaveFileLocallyHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Savig file locally")
        context.payment_book.save_to_file(filename="Oplaty.xlsm")
        print(f'{"=" * 60}')
        return super().handle(context)


class MailingHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Sending Mail")
        mailer = Mailer(context.gmail_user, context.gmail_pass, context.payment_book)
        mailer.login()
        mailer.send(context.recipient_email)
        print(f'{"=" * 60}')
        return super().handle(context)


class FileCommitHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        print("Commiting file")
        context.dropbox_client.commit_file("Oplaty.xlsm", context.excel_file_path)
        print(f'{"=" * 60}')
        return super().handle(context)
