from datetime import datetime
from typing import List

import config
from dropbox_client import DropboxClient
from ekartoteka import Ekartoteka
from payment_book import PaymentBook
from payment_list_item import PaymentListItem
from pushover import Pushover
import click
import payment_book as pb


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
    print(f'{"="*60}')
    pu = Pushover(config.pushover_apikey, config.pushover_user)
    dbx = DropboxClient(config.api_key)
    if not noexcel:
        wpk = process_file(dbx=dbx)
        notify_ongoing_payments(wpk, pu, rundry)
        if not noekart:
            ekartoteka_run(pu, rundry, wpk)
        wpk.save_to_file(filename="Oplaty.xlsm")
        print(f'{"=" * 60}')
        flatlist: List[PaymentListItem] = wpk.payment_list
        for list_item in flatlist:
            print(list_item)
        print(f'{"=" * 60}')
        flatlist_sorted = pb.sort_payment_list_by_date(flatlist)
        for list_item2 in flatlist_sorted:
            print(list_item2)
        if not nocommit:
            dbx.commit_file("Oplaty.xlsm", config.excel_file_path)


def process_file(dbx: DropboxClient):
    downloaded_bytes = dbx.retrieve_file(config.excel_file_path)
    payment_book: PaymentBook = PaymentBook(config.monitored_sheets)
    payment_book.load_and_process(downloaded_bytes)
    print("Monitored Columns")
    for name, mk in config.monitored_sheets.items():
        print(f'{name} - {mk}')
    print(f'{"=" * 60}')
    return payment_book


def notify_ongoing_payments(payment_book: PaymentBook, pu: Pushover, rundry: bool):
    print("Notify payments payable in 2 days ")
    for payment_sheet in payment_book.sheets.values():
        cats = payment_sheet.categories.values()
        for category in cats:
            current_key = f'{datetime.now().year}-{datetime.now().month}'
            notify_payload = f"{payment_sheet.name}:{category} " \
                             f"- {(category.payments[current_key])}"

            if category.payments[current_key].payable_within_2days:
                print(notify_payload)
                if not rundry:
                    pu.notify(notify_payload)
    print(f'{"=" * 60}')


def ekartoteka_run(pu, rundry, wpk):
    ekart = Ekartoteka(config.ekartoteka)
    ekart.initialize()
    apartment_fee = ekart.get_curret_fees_sum()
    print("---------- Ekartoteka ---------------------------")
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
