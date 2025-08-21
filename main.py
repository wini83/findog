import os
import sys
from pathlib import Path

import click
from loguru import logger

from handlers.analyticshandler import AnalyticsHandler
from handlers.context import HandlerContext
from handlers.ekartotekahandler import EkartotekaHandler
from handlers.eneahandler import EneaHandler
from handlers.filehandlers import (FileCommitHandler, FileDownloadHandler,
                                   FileProcessHandler, NotifyOngoingHandler,
                                   SaveFileLocallyHandler)
from handlers.handler import Handler
from handlers.iprzedszkolehandler import IPrzedszkoleHandler
from handlers.mailinghandler import MailingHandler
from handlers.njuhandler import NjuHandler
from settings import Settings

API_EKARTOTEKA = "ekartoteka"
API_IPRZEDSZKOLE = "iprzedszkole"
API_ENEA = "enea"
API_NJU = "nju"

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


logger.remove()


logger.add(
    LOG_DIR / "findog.log",
    rotation="1 week",
    retention="14 days",
    enqueue=True,
    backtrace=False,
    diagnose=False
)

logger.add(sys.stdout, level="INFO")

def get_handler(current_handler: Handler, starter: Handler, new_handler: Handler):
    if current_handler is None:
        return new_handler, new_handler
    else:
        return current_handler.set_next(new_handler), starter


def load_settings()->Settings:
    return Settings.from_all()

@click.command(no_args_is_help=True)
@click.option("--enable-all", is_flag=True, help="Carry out the full process", default=False, )
@click.option("--enable-dropbox", is_flag=True, help="Run with processing excel file, ignored with '--enable-all'",
              default=False)
@click.option("--enable-notification", is_flag=True, help="Run with notifications,ignored with '--enable-all'",
              default=False)
@click.option("--enable-api-all", is_flag=True, help="Run with all API clients, ignored with '--enable-all'",
              default=False)
@click.option("--enable-analytics", is_flag=True, help="Run with Analytics module, ignored with '--enable-all'",
              default=False)
@click.option("--enable-api", help="Enable specific api, ignored with '--enable-all'", multiple=True)
@click.option("--disable-commit", is_flag=True, help="Run without committing file to dropbox", default=False)
def main(enable_all,
         enable_dropbox,
         enable_notification,
         enable_api_all,
         enable_api,
         enable_analytics,
         disable_commit
         ):
    """
A simple program to keep your payments in check
    """
    click.echo(click.style('Findog - simple program to keep your payments in check',
                           fg='black',
                           bold=True,
                           bg="yellow",
                           blink=True))
    click.echo(f'{"=" * 60}')
    logger.info("Findog - simple program to keep your payments in check")
    if enable_all:
        enable_dropbox = True
        enable_notification = True
        enable_api_all = True
    if enable_api_all:
        enable_api = (API_EKARTOTEKA, API_IPRZEDSZKOLE, API_ENEA, API_NJU)
    settings = load_settings()
    ctx = HandlerContext(silent=not enable_notification, settings=settings)
    notifier = NotifyOngoingHandler()
    mailer = MailingHandler()
    mailer.run_dry = not enable_notification

    # noinspection PyTypeChecker
    starter: Handler = None
    # noinspection PyTypeChecker
    handler: Handler = None

    if enable_dropbox:
        starter = FileDownloadHandler()
        handler = starter.set_next(FileProcessHandler())
    else:
        ctx.no_excel = True

    if API_EKARTOTEKA in enable_api:
        poller_ekartoteka = EkartotekaHandler()
        handler, starter = get_handler(handler, starter, poller_ekartoteka)
    if API_IPRZEDSZKOLE in enable_api:
        poller_iprzedszkole = IPrzedszkoleHandler()
        handler, starter = get_handler(handler, starter, poller_iprzedszkole)
    if API_ENEA in enable_api:
        poller_enea = EneaHandler()
        handler, starter = get_handler(handler, starter, poller_enea)
    if API_NJU in enable_api:
        poller_nju = NjuHandler()
        handler, starter = get_handler(handler, starter, poller_nju)

    if enable_dropbox:
        if enable_notification:
            handler = handler.set_next(notifier)
            handler = handler.set_next(mailer)
        if enable_analytics:
            anal = AnalyticsHandler()
            handler = handler.set_next(anal)
        handler = handler.set_next(SaveFileLocallyHandler())
        if not disable_commit:
            handler.set_next(FileCommitHandler())
    # Fire!!
    if starter is not None:
        starter.handle(ctx)


if __name__ == '__main__':
    main()
