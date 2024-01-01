import datetime

from loguru import logger

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
from iprzedszkole import Iprzedszkole, Receivables


class IPrzedszkoleHandler(AbstractHandler):

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
            if not context.no_excel:
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
        except Exception as e:
            logger.exception("Problem with iPrzedszkole", exc_info=e)
            context.pushover.error("Problem with iprzedszkole")
        return super().handle(context)

    def __str__(self):
        return "iPrzedszkole"
