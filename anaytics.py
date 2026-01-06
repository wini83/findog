import datetime

from payment_book import PaymentBook


def key_2_date(key: str):
    elements = key.split("-")
    years = int(elements[0])
    months = int(elements[1])
    return datetime.date(years, months, 1)


def generate_dataframe(payment_book: PaymentBook):
    result = {}
    for key_sheet, sheet in payment_book.sheets.items():
        for key_category, category in sheet.categories.items():
            for key_payment, payment in category.payments.items():
                date_index = key_2_date(key_payment)
                if result.get(date_index):
                    result[key_2_date(key_payment)][f'{key_sheet}/{key_category}'] = (
                        payment.amount
                    )
                else:
                    result[key_2_date(key_payment)] = {
                        f'{key_sheet}/{key_category}': payment.amount
                    }

    return result
