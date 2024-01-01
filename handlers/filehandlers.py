import sys

from loguru import logger

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
from payment_list_item import PaymentListItem


class FileDownloadHandler(AbstractHandler):
    # noinspection PyBroadException
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Downloading File...")
        if context is not None:
            try:
                context.file_object = context.dropbox_client.retrieve_file(context.excel_file_path)
                logger.info(f"File {context.excel_file_name} downloaded")
                return super().handle(context)
            except Exception:
                # TODO: narrow exception
                logger.exception("Problem with download excel file")
                context.pushover.error("Problem with download excel file")
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
            logger.info(f"File {context.excel_file_name} processed successfully")
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


class SaveFileLocallyHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Saving file locally")
        context.payment_book.save_to_file(filename=context.excel_file_name)
        logger.info(f"File: {context.excel_file_name} saved")
        return super().handle(context)

    def __str__(self):
        return "Save File Locally"


class FileCommitHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Committing file")
        context.dropbox_client.commit_file(context.excel_file_name, context.excel_file_path)
        logger.info(f"file: {context.excel_file_name} committed")
        return super().handle(context)

    def __str__(self):
        return "File Commit"
