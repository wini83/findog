from datetime import datetime

from loguru import logger

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
from api_clients.nju_client import Nju, filter_by_current_period, filter_not_paid, print_summary


class NjuHandler(AbstractHandler):

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("nju")
        try:
            queue_accounts = []
            for account in context.nju_credentials:
                nju_client = Nju(account["phone"], account["password"])
                account_dict = {"client": nju_client, "sheet": account["sheet"], "category": account["cat"]}
                queue_accounts.append(account_dict)
            log_str = "Nju:"
            for account in queue_accounts:
                account["client"].login()
                account["client"].write2file()
                account["invoices"] = account["client"].parse_html()
                account["invoices_current"] = filter_by_current_period(account["invoices"])
                account["invoices_payable"] = filter_not_paid(account["invoices"])
                log_str += "{"
                log_str += f"phone:{account['client'].phone_nmb} - "
                log_str += print_summary(account["invoices_payable"], text_if_none="no unpaid invoices")
                log_str += "}"
                if not context.no_excel:
                    if len(account["invoices_current"]) > 0:
                        total: float = 0.0
                        paid: bool = True
                        due_date = datetime.combine(account["invoices_current"][0].due_date, datetime.min.time())
                        for invoice in account["invoices_current"]:
                            total += invoice.total()
                            if not invoice.status_bool:
                                paid = False
                        context.payment_book.update_current_payment(
                            sheet_name=account["sheet"],
                            category_name=account["category"],
                            amount=total,
                            paid=paid,
                            due_date=due_date,
                            force_unpaid=True
                        )

            logger.info(log_str)
            context.statuses.append(log_str)
        except Exception as e:
            logger.exception("Problem with nju", exc_info=e)
            context.pushover.error("Problem with nju")
        return super().handle(context)

    def __str__(self):
        return "Nju"
