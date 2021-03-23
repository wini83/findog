from datetime import datetime

import config
from dropbox_client import DropboxClient
from ekartoteka import Ekartoteka
from payment_book import PaymentBook
from pushover import Pushover


def download_file():
    downloaded_bytes = dbx.retrieve_file(config.excel_file_path)
    payment_book: PaymentBook = PaymentBook(config.monitored_sheets)
    payment_book.load_from_file(downloaded_bytes)
    print("-----------------------------------------")

    for name, mk in config.monitored_sheets.items():
        print(f'{name} - {mk}')

    print("-----------------------------------------")
    return payment_book


def notify(payment_book: PaymentBook):
    for payment_sheet in payment_book.sheets:
        cats = payment_sheet.categories
        for category in cats:
            print(f"{payment_sheet.name}:{category} - {(category.payments[0])}")
            if category.payments[0].payable_within_2days:
                pu.notify(f"{category} - {(category.payments[0])}")


if __name__ == '__main__':
    pu = Pushover(config.pushover_apikey, config.pushover_user)
    dbx = DropboxClient(config.api_key)
    wpk = download_file()
    notify(wpk)
    getter = Ekartoteka(config.ekartoteka)
    getter.initialize()
    apartment_fee = getter.get_curret_fees_sum()
    print(apartment_fee)
    res_setl, delta = getter.get_settlements_sum(datetime.now().year)
    if res_setl:
        pu.notify(f'Mieszkanie: {apartment_fee:.2f} zł, pozostało do zapłaty {delta:.2f} zł')
    else:
        pu.notify(f'Mieszkanie: {apartment_fee:.2f}zł')

    wpk.update_current_payment_amount(config.ekartoteka_sheet[0], config.ekartoteka_sheet[1], apartment_fee)
    wpk.save_to_file(filename="Oplaty.xlsm")
