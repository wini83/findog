import click

from context import HandlerContext
from handlers_tmp import SaveFileLocallyHandler, NotifyOngoingHandler, MailingHandler, EkartotekaHandler, \
    FileDownloadHandler, FileProcessHandler, FileCommitHandler, IPrzedszkoleHandler
from handlers.eneahandler import EneaHandler
from handlers.njuhandler import NjuHandler
from loguru import logger

from os import chdir, path

chdir(path.dirname(path.abspath(__file__)))

logger.add("./logs/findog.log", rotation="1 week")


@click.command()
@click.option("--silent", is_flag=True, help="Run without notifications", default=False)
@click.option("--noekart", is_flag=True, help="Run without Ekartoteka", default=False)
@click.option("--nocommit", is_flag=True, help="Run without committing file to dropbox", default=False)
@click.option("--mailrundry", is_flag=True, help="Run without sending mail", default=False)
@click.option("--noexcel", is_flag=True, help="in experimental mode", default=False)
@click.option("--noiprzed", is_flag=True, help="Run without Iprzedszkole", default=False)
@click.option("--noenea", is_flag=True, help="Run without enea", default=False)
def main(silent, noekart, nocommit, mailrundry, noexcel, noiprzed, noenea):
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
    ctx = HandlerContext(silent=silent)
    fd = FileDownloadHandler()
    fp = FileProcessHandler()
    no = NotifyOngoingHandler()
    ek = EkartotekaHandler()
    ip = IPrzedszkoleHandler()
    nj = NjuHandler()
    sv = SaveFileLocallyHandler()
    ma = MailingHandler()
    ma.run_dry = mailrundry
    fc = FileCommitHandler()
    en = EneaHandler()
    if not noexcel:
        handler = fd.set_next(fp)
        if not silent:
            handler = handler.set_next(no)
        if not noekart:
            handler = handler.set_next(ek)
        if not noiprzed:
            handler = handler.set_next(ip)
        if not noenea:
            handler = handler.set_next(en)
        #if not silent: TODO: better logic silent
        handler = handler.set_next(nj)
        handler = handler.set_next(ma)
        handler = handler.set_next(sv)
        if not nocommit:
            handler.set_next(fc)
        fd.handle(ctx)
    else:
        ek.without_update = True
        if not noekart:
            ek.handle(ctx)
        if not noiprzed:
            ip.handle(ctx)
        if not noenea:
            en.handle(ctx)
        nj.handle(ctx)



if __name__ == '__main__':
    main()
