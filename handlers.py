import os
import sys
from abc import ABC, abstractmethod

from context import HandlerContext
from ekartoteka import Ekartoteka
from mailer import Mailer
from payment_list_item import PaymentListItem

from loguru import logger


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
        logger.info(f'Handler: {self.__str__()} - next handler is {handler.__str__()}')
        return handler

    @abstractmethod
    def handle(self, context: HandlerContext) -> HandlerContext:
        if self._next_handler:
            return self._next_handler.handle(context)
        return context


class FileDownloadHandler(AbstractHandler):
    # noinspection PyBroadException
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Downloading File...")
        if context is not None:
            try:
                context.file_object = context.dropbox_client.retrieve_file(context.excel_file_path)
                logger.info(f"File {context.excel_file_path} downloaded")
                return super().handle(context)
            except Exception as e:
                # TODO: narrow excepion
                logger.exception("Problem with download")
                sys.exit(1)

    def __str__(self):
        return "File download"


class FileProcessHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Processing Excel File")
        logger.info("Input - Monitored Columns")
        if context.file_object is not None and context.payment_book is not None:
            for name, mk in context.payment_book.monitored_sheets.items():
                logger.info(f'{name} - {mk}')
            context.payment_book.load_and_process(context.file_object)
            logger.info(f"File {context.excel_file_path} processed succesfully")
            return super().handle(context)
        else:
            logger.error("Context not initialized")
            sys.exit(0)

    def __str__(self):
        return "File process"


class NotifyOngoingHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Notify payments payable in 2 days")
        pmt_list: list[PaymentListItem] = context.payment_book.payment_list
        payload: str = ""
        i: int = 0
        for item in pmt_list:
            if item.payment.payable_within_2days:
                new_str = item.__str__() + "\n"
                payload += new_str
                i += 1
        if i > 0:
            context.pushover.notify(payload)
        else:
            payload = "None :)"
        logger.info(f'payments:{payload}')
        return super().handle(context)

    def __str__(self):
        return "Notify Ongoing Payments"


class EkartotekaHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Ekartoteka")
        ekart = Ekartoteka(context.ekartoteka_creditentials, context.payment_book)
        ekart.login()
        apartment_fee, delta = ekart.update_payment_book(context.ekartoteka_sheet[0], context.ekartoteka_sheet[1])
        ekart_str = f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł'
        logger.info(ekart_str)
        if not context.silent and delta != 0:
            context.pushover.notify(f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł')
        return super().handle(context)

    def __str__(self):
        return "Ekartoteka"


class SaveFileLocallyHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Savig file locally")
        context.payment_book.save_to_file(filename="Oplaty.xlsm")
        logger.info("file: Oplaty.xlsm saved")
        return super().handle(context)

    def __str__(self):
        return "Save File Locally"


class MailingHandler(AbstractHandler):
    rundry: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:

        mailer = Mailer(context.gmail_user, context.gmail_pass, context.payment_book)
        mailer.login()
        logger.info("Rendering message")
        payload = mailer.render()
        logger.info("Rendering completed")
        if not self.rundry:
            logger.info(f"There are {len(context.recipients)} mail(s) to send")
            for recipient in context.recipients:
                mailer.send(recipient, payload)
                logger.info(f"mail to {recipient} send")
            logger.info("sending mail completed")
        else:
            with open("output_mail.html", "wb") as html_file:
                html_file.write(payload.encode('utf-8'))
        return super().handle(context)

    def __str__(self):
        return "Send Mails"


class FileCommitHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Commiting file")
        context.dropbox_client.commit_file("Oplaty.xlsm", context.excel_file_path)
        logger.info("file: Oplaty.xlsm commited")
        return super().handle(context)

    def __str__(self):
        return "File Commit"
