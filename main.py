from datetime import datetime

import config
from dropbox_client import DropboxClient
from ekartoteka import Ekartoteka
from payment_book import PaymentBook
from pushover import Pushover
import click


def download_file(dbx: DropboxClient):
    downloaded_bytes = dbx.retrieve_file(config.excel_file_path)
    payment_book: PaymentBook = PaymentBook(config.monitored_sheets)
    payment_book.load_from_file(downloaded_bytes)
    print("-----------------------------------------")

    for name, mk in config.monitored_sheets.items():
        print(f'{name} - {mk}')

    print("-----------------------------------------")
    return payment_book


def notify_ongoing_payments(payment_book: PaymentBook, pu: Pushover, rundry: bool):
    for payment_sheet in payment_book.sheets:
        cats = payment_sheet.categories
        for category in cats:
            print(f"{payment_sheet.name}:{category} - {(category.payments[0])}")
            if category.payments[0].payable_within_2days and not rundry:
                pu.notify(f"{category} - {(category.payments[0])}")


@click.command()
@click.option("--rundry", is_flag=True, help="Run without notifications", default=False)
@click.option("--noekart", is_flag=True, help="Run without Ekartoteka", default=False)
@click.option("--noexcel", is_flag=True, help="Run without Excel file", default=False)
@click.option("--nocommit", is_flag=True, help="Run without commiting file to dropbox", default=False)
def main(rundry, noekart, noexcel,nocommit):
    """
A simple program to keep your payments in check
    """
    click.echo(click.style('Findog - simple program to keep your payments in check',
                           fg='black',
                           bold=True,
                           bg="yellow",
                           blink=True))
    pu = Pushover(config.pushover_apikey, config.pushover_user)
    dbx = DropboxClient(config.api_key)
    if not noexcel:
        wpk = download_file(dbx=dbx)
        notify_ongoing_payments(wpk, pu, rundry)
        if not noekart:
            ekartoteka_run(pu, rundry, wpk)
        wpk.save_to_file(filename="Oplaty.xlsm")
        if not nocommit:
            dbx.commit_file("Oplaty.xlsm", config.excel_file_path)

def ekartoteka_run(pu, rundry, wpk):
    ekart = Ekartoteka(config.ekartoteka)
    ekart.initialize()
    apartment_fee = ekart.get_curret_fees_sum()
    print("-----------------------------------")
    print(f'Mieszkanie: {apartment_fee:.2f}zł')
    res_setl, delta = ekart.get_settlements_sum(datetime.now().year)
    if not rundry:
        if res_setl:
            pu.notify(f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł')
        else:
            pu.notify(f'Mieszkanie: {apartment_fee:.2f}zł')

    if res_setl and delta is not None:
        if delta > 0:
            paid = False
        else:
            paid = True
    else:
        paid = None

    wpk.update_current_payment(config.ekartoteka_sheet[0], config.ekartoteka_sheet[1], apartment_fee, paid=paid)


if __name__ == '__main__':
    main()
