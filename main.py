import string
from datetime import datetime
from io import BytesIO

import dropbox
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

import config
from payment import Payment
from payment_category import PaymentCategory


def download_file():
    dbx = dropbox.Dropbox(config.api_key)
    metadata, res = dbx.files_download(path=config.excel_file_path)
    return res.content


def get_sheet_from_file(sheet_name: string, file: bytes):
    workbook = load_workbook(filename=BytesIO(file))
    return workbook[sheet_name]


def get_active_row(sheet: Worksheet):
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_row = 2
    while sheet[f"A{current_row}"].value is not None:
        date_item = sheet[f"A{current_row}"].value
        if (date_item.month == current_month) and (date_item.year == current_year):
            break
        current_row += 1
    return current_row


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    downloaded_bytes = download_file()

    we_sheet = get_sheet_from_file(sheet_name=config.workbook_name, file=downloaded_bytes)
    active_row = get_active_row(we_sheet)

    categories = []

    for column in config.active_categories:
        name = we_sheet[f"{column}1"].value
        item = PaymentCategory(name=name, column=column)
        amount = float(we_sheet[f"{column}{active_row}"].value)

        column_int = we_sheet[f"{column}{active_row}"].col_idx

        try:
            done = bool(we_sheet.cell(column=column_int + 1, row=active_row).value)
        except ValueError:
            done = False

        due_date = we_sheet.cell(column=column_int + 2, row=active_row).value
        item.payments.append(Payment(payed=done, amount=amount, due_date=due_date, excel_row=active_row))

        categories.append(item)

    for category in categories:
        if not category.payments[0].payed:
            print(f"{category} - {(category.payments[0])}")
