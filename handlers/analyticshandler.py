from loguru import logger

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler


class AnalyticsHandler(AbstractHandler):
    run_dry: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:

        try:
            if not self.run_dry:

                logger.info("Analytics completed")
        except Exception as e:
            logger.exception("Problem with Analytics", exc_info=e)
            context.pushover.error("Problem with Analytics")
        return super().handle(context)

    def __str__(self):
        return "Analytics"
