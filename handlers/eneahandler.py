"""Handler for ENEA electricity portal extracting invoice data."""

from datetime import datetime

from loguru import logger

from api_clients.enea import Enea, EneaResults
from handlers.context import HandlerContext
from handlers.handler import AbstractHandler


class EneaHandler(AbstractHandler):
    """Update book with ENEA invoice status for the current month."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Fetch and log ENEA data; update payment book if applicable."""
        logger.info("Enea")
        try:
            enea = Enea(
                context.enea_credentials["username"],
                context.enea_credentials["password"],
            )
            enea.login()
            enea_results: EneaResults = enea.get_data()
            enea_str = (
                f'ENEA: '
                f'Last invoice issue date: {enea_results.last_invoice_date:%Y-%m-%d}; '
                f'Last invoice due date: '
                f'{enea_results.last_invoice_due_date:%Y-%m-%d}; '
                f'Last invoice amount PLN: '
                f'{enea_results.last_invoice_amount_pln:.2f}; '
                f'Last invoice unpaid PLN: {enea_results.last_invoice_unpaid_pln:.2f}; '
                f'Last invoice status: {enea_results.last_invoice_status}; '
                f'Last readout date: {enea_results.last_readout_date:%Y-%m-%d};'
                f'Last readout value kWh: {enea_results.last_readout_amount_kwh:.2f}'
            )

            if enea_results.last_invoice_unpaid_pln > 0:
                paid = False
            else:
                paid = True
            if not context.no_excel:
                today = datetime.now()
                if (
                    enea_results.last_invoice_due_date.month == today.month
                    and enea_results.last_invoice_due_date.year == today.year
                ):
                    context.payment_book.update_current_payment(
                        sheet_name=context.enea_sheet[0],
                        category_name=context.enea_sheet[1],
                        amount=enea_results.last_invoice_amount_pln,
                        paid=paid,
                        due_date=enea_results.last_invoice_due_date,
                    )
                else:
                    enea_str += " !Enea not updated in excel!"
            logger.info(enea_str)
            context.statuses.append(enea_str)
        except Exception as e:
            logger.exception("Problem with Enea", exc_info=e)
            context.pushover.error("Problem with Enea")
        return super().handle(context)

    def __str__(self):
        return "Enea"
