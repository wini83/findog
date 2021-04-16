import click

from context import HandlerContext
from handlers import SaveFileLocallyHandler, NotifyOngoingHandler, MailingHandler, EkartotekaHandler, \
    FileDownloadHandler, FileProcessHandler, FileCommitHandler


@click.command()
@click.option("--silent", is_flag=True, help="Run without notifications", default=False)
@click.option("--noekart", is_flag=True, help="Run without Ekartoteka", default=False)
@click.option("--nocommit", is_flag=True, help="Run without commiting file to dropbox", default=False)
def main(silent, noekart, nocommit):
    """
A simple program to keep your payments in check
    """
    click.echo(click.style('Findog - simple program to keep your payments in check',
                           fg='black',
                           bold=True,
                           bg="yellow",
                           blink=True))
    print(f'{"=" * 60}')
    ctx = HandlerContext(silent=silent)
    fd = FileDownloadHandler()
    fp = FileProcessHandler()
    no = NotifyOngoingHandler()
    ek = EkartotekaHandler()
    sv = SaveFileLocallyHandler()
    ma = MailingHandler()
    fc = FileCommitHandler()

    handler = fd.set_next(fp)

    if not silent:
        handler = handler.set_next(no)

    if not noekart:
        handler = handler.set_next(ek)

    handler = handler.set_next(sv)

    if not silent:
        handler = handler.set_next(ma)

    if not nocommit:
        handler = handler.set_next(fc)

    print(type(handler))

    fd.handle(ctx)


if __name__ == '__main__':
    main()
