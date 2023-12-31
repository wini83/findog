import click

from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
from handlers_tmp import SaveFileLocallyHandler, NotifyOngoingHandler, MailingHandler, FileDownloadHandler, \
    FileProcessHandler, FileCommitHandler, IPrzedszkoleHandler
from handlers.ekartotekahandler import EkartotekaHandler
from handlers.eneahandler import EneaHandler
from handlers.njuhandler import NjuHandler
from loguru import logger

from os import chdir, path

API_EKARTOTEKA = "ekartoteka"
API_IPRZEDSZKOLE = "iprzedszkole"
API_ENEA = "enea"
API_NJU = "nju"

chdir(path.dirname(path.abspath(__file__)))

logger.add("./logs/findog.log", rotation="1 week")


def get_default_handler(handler: AbstractHandler, starter: AbstractHandler, default_handler: AbstractHandler):
    if handler is None:
        return default_handler, default_handler
    else:
        return handler.set_next(default_handler), starter


@click.command(no_args_is_help=True)
@click.option("--enable-all", is_flag=True, help="Carry out the full process", default=False, )
@click.option("--enable-dropbox", is_flag=True, help="Run with processing excel file, ignored with '--enable-all'",
              default=False)
@click.option("--enable-notification", is_flag=True, help="Run without notifications,ignored with '--enable-all'",
              default=False)
@click.option("--enable-api-all", is_flag=True, help="Run without all API clients, ignored with '--enable-all'",
              default=False)
@click.option("--enable-api", help="Enable specific api, ignored with '--enable-all'", multiple=True)
@click.option("--disable-commit", is_flag=True, help="Run without committing file to dropbox", default=False)
def main(enable_all,
         enable_dropbox,
         enable_notification,
         enable_api_all,
         enable_api,
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
    ctx = HandlerContext(silent=not enable_notification)
    notifier = NotifyOngoingHandler()
    mailer = MailingHandler()
    mailer.run_dry = not enable_notification

    starter: AbstractHandler = None
    handler: AbstractHandler = None

    if enable_dropbox:
        file_downloader = FileDownloadHandler()
        file_processor = FileProcessHandler()
        file_saver = SaveFileLocallyHandler()
        file_committer = FileCommitHandler()
        starter = file_downloader
        handler = file_downloader.set_next(file_processor)
    else:
        ctx.no_excel = True

    if API_EKARTOTEKA in enable_api:
        poller_ekartoteka = EkartotekaHandler()
        handler, starter = get_default_handler(handler, starter, poller_ekartoteka)
    if API_IPRZEDSZKOLE in enable_api:
        poller_iprzedszkole = IPrzedszkoleHandler()
        handler, starter = get_default_handler(handler, starter, poller_iprzedszkole)
    if API_ENEA in enable_api:
        poller_enea = EneaHandler()
        handler, starter = get_default_handler(handler, starter, poller_enea)
    if API_NJU in enable_api:
        poller_nju = NjuHandler()
        handler, starter = get_default_handler(handler, starter, poller_nju)

    if enable_dropbox:
        if enable_notification:
            handler = handler.set_next(notifier)
        handler = handler.set_next(mailer)
        handler = handler.set_next(file_saver)
        if not disable_commit:
            handler.set_next(file_committer)
    # Fire!!
    if starter is not None:
        starter.handle(ctx)


if __name__ == '__main__':
    main()
