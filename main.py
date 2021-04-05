import click

import config
from dropbox_client import DropboxClient
from ekartoteka import Ekartoteka
from mailer import Mailer
from payment_book import PaymentBook
from pushover import Pushover, PushoverNotifier


@click.command()
@click.option("--rundry", is_flag=True, help="Run without notifications", default=False)
@click.option("--noekart", is_flag=True, help="Run without Ekartoteka", default=False)
@click.option("--noexcel", is_flag=True, help="Run without Excel file", default=False)
@click.option("--nocommit", is_flag=True, help="Run without commiting file to dropbox", default=False)
def main(rundry, noekart, noexcel, nocommit):
    """
A simple program to keep your payments in check
    """
    click.echo(click.style('Findog - simple program to keep your payments in check',
                           fg='black',
                           bold=True,
                           bg="yellow",
                           blink=True))
    print(f'{"=" * 60}')
    pu = Pushover(config.pushover_apikey, config.pushover_user)
    dbx = DropboxClient(config.api_key)
    if not noexcel:
        wpk = process_file(dbx=dbx)
        print(f'{"=" * 60}')
        notify_ongoing_payments(wpk, pu, rundry)
        print(f'{"=" * 60}')
        if not noekart:
            ekartoteka_run(pu, rundry, wpk)
            print(f'{"=" * 60}')
        wpk.save_to_file(filename="Oplaty.xlsm")

        if not rundry:
            print("Sending Mail")
            mailer = Mailer(config.gmail_user, config.gmail_pass, wpk)
            mailer.login()
            mailer.send(config.recipient_email)
            print(f'{"=" * 60}')

        if not nocommit:
            print("Commiting file")
            dbx.commit_file("Oplaty.xlsm", config.excel_file_path)
            print(f'{"=" * 60}')


def process_file(dbx: DropboxClient):
    downloaded_bytes = dbx.retrieve_file(config.excel_file_path)
    payment_book: PaymentBook = PaymentBook(config.monitored_sheets)
    payment_book.load_and_process(downloaded_bytes)
    print("Monitored Columns")
    for name, mk in config.monitored_sheets.items():
        print(f'{name} - {mk}')
    return payment_book


def notify_ongoing_payments(payment_book: PaymentBook, pu: Pushover, rundry: bool):
    print("Notify payments payable in 2 days ")
    pun = PushoverNotifier(pushover=pu, payment_book=payment_book)
    pun.login()
    pun_str = pun.notify_ongoing_payments(rundry)
    if pun_str == "":
        pun_str = "None :)"
    print(pun_str)


def ekartoteka_run(pu, rundry, wpk):
    print("Ekartoteka")
    ekart = Ekartoteka(config.ekartoteka, wpk)
    ekart.login()
    apartment_fee, delta = ekart.update_payment_book(config.ekartoteka_sheet[0], config.ekartoteka_sheet[1])
    ekart_str = f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł'
    print(ekart_str)
    if not rundry:
        pu.notify(f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł')


if __name__ == '__main__':
    main()
