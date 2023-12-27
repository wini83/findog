import datetime

from loguru import logger

from api_clients.enea import Enea, EneaResults
from context import HandlerContext
from handlers.handler import AbstractHandler


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