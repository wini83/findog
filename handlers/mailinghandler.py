"""Handler responsible for rendering and sending email reports."""

from loguru import logger

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
from mailer import Mailer


class MailingHandler(AbstractHandler):
    """Uses Mailer to produce HTML and send it to recipients."""

    run_dry: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        """Render report HTML and optionally send emails."""

        mailer = Mailer(context.gmail_user, context.gmail_pass, context.payment_book)
        mailer.statuses = context.statuses
        # noinspection PyBroadException
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
                with open("/data/output_mail.html", "wb") as html_file:
                    html_file.write(payload.encode('utf-8'))
        except Exception:  # pylint: disable=broad-except #edge of system
            logger.exception("Problem with Mailer")
            context.pushover.error("Problem with mailer")
        return super().handle(context)

    def __str__(self):
        return "Mailer"
