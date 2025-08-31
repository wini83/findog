"""Handler for e-kartoteka service to sync apartment fees."""

from loguru import logger

from api_clients.ekartoteka import Ekartoteka
from handlers.context import HandlerContext
from handlers.handler import AbstractHandler


class EkartotekaHandler(AbstractHandler):
    """Queries e-kartoteka and updates current month payment."""

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Fetch payment data and update payment book; log status."""
        logger.info("Ekartoteka")
        ekartoteka_client = Ekartoteka(context.ekartoteka_credentials)
        ekartoteka_client.login()
        result = ekartoteka_client.get_payment_status()

        if not context.no_excel:
            context.payment_book.update_current_payment(
                sheet_name=context.ekartoteka_sheet[0],
                category_name=context.ekartoteka_sheet[1],
                amount=result.apartment_fee,
                paid=result.paid,
                force_unpaid=result.force_unpaid,
            )
        log_str = (
            'EKARTOTEKA: '
            f'apartment fee: PLN {result.apartment_fee:.2f} , '
            f'unpaid: PLN {result.delta:.2f} '
            'Updates: '
        )
        for key, value in result.update_dates.items():
            log_str = log_str + f' {key}-{value:%Y-%m-%d};'
        logger.info(log_str)
        context.statuses.append(log_str)
        return super().handle(context)

    def __str__(self):
        return "Ekartoteka"
