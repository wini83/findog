"""Handlers for file download, processing, notifications and commits."""

import sys

from loguru import logger

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
from payment_list_item import PaymentListItem


class FileDownloadHandler(AbstractHandler):
    """Download the Excel file from Dropbox into memory."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Retrieve file bytes using Dropbox client and pass along the chain."""
        logger.info("Downloading File...")
        if context is None:
            logger.error("Context is None in FileDownloadHandler")
            return None
        try:
            context.file_object = context.dropbox_client.retrieve_file(
                context.excel_dropbox_path
            )
            logger.info(f"File {context.excel_file_name} downloaded")
            return super().handle(context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # NOTE: Dropbox client may raise various exceptions; catching broadly here
            # keeps the pipeline resilient and delegates user notification.
            logger.exception("Problem with download excel file: %s", exc)
            context.pushover.error("Problem with download excel file")
            if getattr(context, "silent", False):
                return context
            sys.exit(1)

    def __str__(self):
        """Human-readable name for logs."""
        return "File download"


class FileProcessHandler(AbstractHandler):
    """Process the downloaded Excel file and populate payment structures."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Load workbook, populate categories/month and continue the chain."""
        logger.info("Processing Excel File")
        logger.info("Input - Monitored Columns")
        if context.file_object is not None and context.payment_book is not None:
            for name, mk in context.payment_book.monitored_sheets.items():
                logger.info(f'{name} - {mk}')
            context.payment_book.load_and_process(context.file_object)
            logger.info(f"File {context.excel_file_name} processed successfully")
            return super().handle(context)
        logger.error("Context not initialized")
        if getattr(context, "silent", False):
            return context
        sys.exit(0)

    def __str__(self):
        """Human-readable name for logs."""
        return "File process"


class NotifyOngoingHandler(AbstractHandler):
    """Send a list of payments due within two days via Pushover."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Build a message of imminent payments and notify if any exist."""
        logger.info("Notify payments payable in 2 days")
        pmt_list: list[PaymentListItem] = context.payment_book.payment_list
        payload: str = ""
        i: int = 0
        for item in pmt_list:
            if item.payment.due_soon_or_overdue:
                new_str = str(item) + "\n"
                payload += new_str
                i += 1
        if i > 0:
            context.pushover.notify(payload)
        if i == 0:
            payload = "None :)"
        logger.info(f'payments:{payload}')
        return super().handle(context)

    def __str__(self):
        """Human-readable name for logs."""
        return "Notify Ongoing Payments"


class SaveFileLocallyHandler(AbstractHandler):
    """Save the modified workbook to a local path."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Write workbook to disk and continue the chain."""
        logger.info("Saving file locally")
        context.payment_book.save_to_file(filename=context.excel_local_path)
        logger.info(f"File: {context.excel_file_name} saved")
        return super().handle(context)

    def __str__(self):
        """Human-readable name for logs."""
        return "Save File Locally"


class FileCommitHandler(AbstractHandler):
    """Commit the local workbook file back to Dropbox."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Upload local file to Dropbox, then continue the chain."""
        logger.info("Committing file")
        context.dropbox_client.commit_file(
            context.excel_local_path, context.excel_dropbox_path
        )
        logger.info(f"file: {context.excel_file_name} committed")
        return super().handle(context)

    def __str__(self):
        """Human-readable name for logs."""
        return "File Commit"
