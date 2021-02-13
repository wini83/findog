import string
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

import config
from dropbox_client import DropboxClient
from payment_book import PaymentBook
from pushover import Pushover


def get_sheet_from_file(sheet_name: string, file: bytes) -> Worksheet:
    workbook = load_workbook(filename=BytesIO(file))
    return workbook[sheet_name]


if __name__ == '__main__':
    dbx = DropboxClient(config.api_key)
    downloaded_bytes = dbx.retrieve_file(config.excel_file_path)
    pu = Pushover(config.pushover_apikey, config.pushover_user)

    wpk = PaymentBook(config.sheets)

    wpk.load_from_file(downloaded_bytes)

    payment_sheet = wpk.sheets[0]

    cats = payment_sheet.categories

    for category in cats:
        if category.payments[0].payable_within_2days:
            print(f"{category} - {(category.payments[0])}")
            pu.notify(f"{category} - {(category.payments[0])}")