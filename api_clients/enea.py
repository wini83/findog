import datetime
import urllib.request
from dataclasses import dataclass
from http.cookiejar import CookieJar

from bs4 import BeautifulSoup

from api_clients.Client import Client


def _extract_amounts_main(bs):
    span = bs.find('div', {'class': 'h1 value-to-pay'})
    amount_str = span.get_text()
    return float(amount_str)


def parse_amount(amount):
    return float(amount.strip().rstrip("zł").strip().replace(",", "."))


def parse_energy(amount):
    return float(amount.replace("\r", "").strip().rstrip("kWh").strip().replace(",", "."))


def get_last_month_int():
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    last_month = last_month.month
    return last_month

@dataclass
class EneaResults:
    last_invoice_date: datetime
    last_invoice_due_date: datetime
    last_invoice_amount_PLN: float
    last_invoice_unpaid_pln: float
    last_invoice_status: str
    last_readout_amount_kWh: float
    last_readout_date: datetime

    def __init__(self, last_invoice_date: datetime,
                 last_invoice_due_date: datetime,
                 last_invoice_amount_pln: float,
                 last_invoice_unpaid_pln: float,
                 last_invoice_status: str,
                 last_readout_amount_kWh: float,
                 last_readout_date: datetime):
        self.last_invoice_date = last_invoice_date
        self.last_invoice_due_date = last_invoice_due_date
        self.last_invoice_amount_PLN = last_invoice_amount_pln
        self.last_invoice_unpaid_pln = last_invoice_unpaid_pln
        self.last_invoice_status = last_invoice_status
        self.last_readout_amount_kWh = last_readout_amount_kWh
        self.last_readout_date = last_readout_date


def _extract_last_invoice(soup):
    row_div = soup.find('div', {'class': 'datagrid-row invoice-row'})
    date_issue_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-invoice-real-date'})
    invoice_date = date_issue_div.get_text()
    invoice_date = strip_div(invoice_date)
    invoice_date = parse_date(invoice_date)
    due_date_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-invoice-real-payment-date'})
    due_date = due_date_div.get_text()
    due_date = strip_div(due_date)
    due_date = parse_date(due_date)
    value_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-invoice-real-value'})
    value = value_div.get_text()
    value = strip_div(value)
    value = parse_amount(value)
    unpaid_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-invoice-real-payment'})
    unpaid = unpaid_div.get_text()
    unpaid = strip_div(unpaid)
    unpaid = parse_amount(unpaid)
    status_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-invoice-status'})
    status = status_div.get_text()
    status = strip_div(status, nested=True)

    return invoice_date, due_date, value, unpaid, status


def _extract_last_readout(soup):
    row_div = soup.find('div', {'class': 'datagrid-row-content'})
    date_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-history-consumption-date'})
    readout_date = date_div.get_text()
    readout_date = strip_div(readout_date)
    readout_date = parse_date(readout_date)
    value_div = row_div.find('div', {'class': 'datagrid-col datagrid-col-history-consumption-value-0'})
    readout_value = value_div.get_text()
    readout_value = strip_div(readout_value)
    readout_value = parse_energy(readout_value)
    return readout_value, readout_date


def parse_date(text: str):
    return datetime.datetime.strptime(text, "%d.%m.%Y")


def strip_div(text: str, nested: bool = False):
    if not nested:
        return text.replace("\n", "")
    else:
        return text.replace("\n\n", "").replace("\n", " ")


class Enea(Client):
    URL_BASE = 'https://ebok.enea.pl'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 ' \
                 'Safari/537.36 '
    URL_LOGIN = "/logowanie"
    URL_INVOICES = "/invoices/invoice-history"
    URL_READOUTS = "/meter/consumptionHistory"

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.userAgent = self.USER_AGENT
        self.opener = None
        self.token = ""
        self.logged_in = False

    def login(self):
        cj = CookieJar()
        # ssl._create_default_https_context = ssl._create_unverified_context
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        request = urllib.request.Request(self.URL_BASE + self.URL_LOGIN)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')

        soup = BeautifulSoup(result, 'html.parser')
        token = soup.find('input', {'name': 'token'})['value']

        form_parameters = {'email': self.email,
                           'password': self.password,
                           'token': token,
                           'btnSubmit': ""
                           }

        form_data = urllib.parse.urlencode(form_parameters)
        request = urllib.request.Request(self.URL_BASE + self.URL_LOGIN)
        request.data = form_data.encode('utf-8')
        request.add_header('User-Agent', self.userAgent)

        result = self.opener.open(request)

        if result.status == 200:
            self.logged_in = True
        else:
            self.logged_in = False
            raise ConnectionError

    def get_data(self) -> EneaResults:

        request = urllib.request.Request(self.URL_BASE + self.URL_INVOICES)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')
        soup = BeautifulSoup(result, 'html.parser')
        invoice_date, due_date, value, unpaid, status = _extract_last_invoice(soup)

        request = urllib.request.Request(self.URL_BASE + self.URL_READOUTS)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')
        soup = BeautifulSoup(result, 'html.parser')
        readout_value, readout_date = _extract_last_readout(soup)
        return EneaResults(last_invoice_date=invoice_date, last_invoice_due_date=due_date,
                           last_invoice_amount_pln=value, last_invoice_unpaid_pln=unpaid, last_invoice_status=status,
                           last_readout_amount_kWh=readout_value, last_readout_date=readout_date)
