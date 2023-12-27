import datetime
import sys
from datetime import datetime

from loguru import logger

from context import HandlerContext
from ekartoteka import Ekartoteka
from api_clients.enea import Enea, EneaResults
from handlers.handler import AbstractHandler
from iprzedszkole import Iprzedszkole, Receivables
from mailer import Mailer
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


class EkartotekaHandler(AbstractHandler):
    without_update: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Ekartoteka")
        ekart = Ekartoteka(context.ekartoteka_credentials)
        ekart.login()
        result = ekart.get_payment_status()

        if not self.without_update:
            context.payment_book.update_current_payment(
                sheet_name=context.ekartoteka_sheet[0],
                category_name=context.ekartoteka_sheet[1],
                amount=result.apartment_fee,
                paid=result.paid,
                force_unpaid=result.force_unpaid)
        ekart_str = \
            f'EKARTOTEKA: apartment fee: PLN {result.apartment_fee:.2f} , unpaid: PLN {result.delta:.2f} Updates: '
        for key, value in result.update_dates.items():
            ekart_str = ekart_str + f' {key}-{value:%Y-%m-%d};'
        logger.info(ekart_str)
        context.statuses.append(ekart_str)
        return super().handle(context)

    def __str__(self):
        return "Ekartoteka"


class IPrzedszkoleHandler(AbstractHandler):
    without_update: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("iPrzedszkole")
        try:
            iprzedszkole = Iprzedszkole(
                context.iprzedszkole_credentials["kindergarten"],
                context.iprzedszkole_credentials["username"],
                context.iprzedszkole_credentials["password"])
            iprzedszkole.login()
            result: Receivables = iprzedszkole.get_receivables()
            if result.summary_overdue > 0:
                paid = False
            else:
                paid = True
            now = datetime.now()
            if now.day < 25:
                force_unpaid = False
            else:
                force_unpaid = True
            if not self.without_update:
                context.payment_book.update_current_payment(
                    sheet_name=context.iprzedszkole_sheet[0],
                    category_name=context.iprzedszkole_sheet[1],
                    amount=result.summary_to_pay,
                    paid=paid,
                    force_unpaid=force_unpaid)
            iprzedszkole_str = \
                f'iPRZEDSZKOLE: fixed costs: PLN {result.costs_fixed:.2f};meal costs: {result.costs_meal:.2f} PLN, ' \
                f'Overdue: PLN {result.summary_overdue:.2f}, ' \
                f'overpaid:PLN {result.summary_overpayment:.2f}, to pay {result.summary_to_pay:.2f}'
            logger.info(iprzedszkole_str)
            context.statuses.append(iprzedszkole_str)
        except:
            logger.exception("Problem with iprzedszkole")
            context.pushover.error("Problem with iprzedszkole")
        return super().handle(context)

    def __str__(self):
        return "iPrzedszkole"


class EneaHandler(AbstractHandler):
    without_update: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Enea")
        try:
            enea = Enea(
                context.enea_credentials["username"],
                context.enea_credentials["password"])
            enea.login()
            enea_results: EneaResults = enea.get_data()
            enea_str = f'ENEA: ' \
                       f'Last invoice issue date: {enea_results.last_invoice_date:%Y-%m-%d}; ' \
                       f'Last invoice due date: {enea_results.last_invoice_due_date:%Y-%m-%d}; ' \
                       f'Last invoice amount PLN: {enea_results.last_invoice_amount_PLN:.2f}; ' \
                       f'Last invoice unpaid PLN: {enea_results.last_invoice_unpaid_pln:.2f}; ' \
                       f'Last invoice status: {enea_results.last_invoice_status}; ' \
                       f'Last readout date: {enea_results.last_readout_date:%Y-%m-%d};' \
                       f'Last readout value kWh: {enea_results.last_readout_amount_kWh:.2f}'

            if enea_results.last_invoice_unpaid_pln > 0:
                paid = False
            else:
                paid = True
            if not self.without_update:
                today = datetime.now()
                if enea_results.last_invoice_due_date.month == today.month \
                        and enea_results.last_invoice_due_date.year == today.year:
                    context.payment_book.update_current_payment(
                        sheet_name=context.enea_sheet[0],
                        category_name=context.enea_sheet[1],
                        amount=enea_results.last_invoice_amount_PLN,
                        paid=paid, due_date=enea_results.last_invoice_due_date)
                else:
                    enea_str += " !Enea not updated in excel!"
            logger.info(enea_str)
            context.statuses.append(enea_str)
        except:
            logger.exception("Problem with Enea")
            context.pushover.error("Problem with Enea")
        return super().handle(context)

    def __str__(self):
        return "Enea"


class SaveFileLocallyHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Saving file locally")
        context.payment_book.save_to_file(filename=context.excel_file_name)
        logger.info(f"File: {context.excel_file_name} saved")
        return super().handle(context)

    def __str__(self):
        return "Save File Locally"


class MailingHandler(AbstractHandler):
    run_dry: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:

        mailer = Mailer(context.gmail_user, context.gmail_pass, context.payment_book)
        mailer.statuses = context.statuses
        try:
            mailer.login()
            logger.info("Rendering message")
            payload = mailer.render()
            logger.info("Rendering completed")
            if not self.run_dry:
                logger.info(f"There are {len(context.recipients)} mail(s) to send")
                for recipient in context.recipients:
                    mailer.send(recipient, payload)
                    logger.info(f"mail to {recipient} send")
                logger.info("sending mail completed")
            else:
                with open("output_mail.html", "wb") as html_file:
                    html_file.write(payload.encode('utf-8'))
        except:
            # TODO: narrow exception
            logger.exception("Problem with Mailer")
            context.pushover.error("Problem with mailer")
        return super().handle(context)

    def __str__(self):
        return "Mailer"


class FileCommitHandler(AbstractHandler):
    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Committing file")
        context.dropbox_client.commit_file(context.excel_file_name, context.excel_file_path)
        logger.info(f"file: {context.excel_file_name} committed")
        return super().handle(context)

    def __str__(self):
        return "File Commit"
