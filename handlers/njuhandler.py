from loguru import logger

from context import HandlerContext
from handlers.handler import AbstractHandler
from nju import Nju, filter_by_current_period


class NjuHandler(AbstractHandler):
    without_update: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("nju")
        try:
            queue_accounts = []
            for account in context.nju_credentials:
                nju_client = Nju(account["phone"], account["password"])
                account_dict = {"client": nju_client, "sheet": account["sheet"], "category": account["cat"]}
                queue_accounts.append(account_dict)


            for account in queue_accounts:
                account["client"].login()
                account["invoices"] = account["client"].parse_html()
                account["invoices_current"] = filter_by_current_period(account["invoices"])

            log_str = "Nju:"
            logger.info(log_str)
            context.statuses.append(log_str)
        except Exception as e:
            logger.exception("Problem with nju", exc_info=e)
            context.pushover.error("Problem with nju")
        return super().handle(context)

    def __str__(self):
        return "Nju"