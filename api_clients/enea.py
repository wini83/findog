"""Scraper for ENEA portal to collect invoices and readouts."""

import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from http.cookiejar import CookieJar

from bs4 import BeautifulSoup, Tag

from api_clients.client import Client


def _extract_amounts_main(bs):
    """Parse the value-to-pay element from the main dashboard."""
    span = bs.find('div', {'class': 'h1 value-to-pay'})
    amount_str = span.get_text()
    return float(amount_str)


def parse_amount(amount):
    """Parse a PLN amount like '12,34zł' into float."""
    return float(amount.strip().rstrip("zł").strip().replace(",", "."))


def parse_energy(amount):
    """Parse an energy value like '1,23 kWh' into float."""
    return float(
        amount.replace("\r", "").strip().rstrip("kWh").strip().replace(",", ".")
    )


def get_last_month_int():
    """Return previous month number as int."""
    today = date.today()
    first = today.replace(day=1)
    last_month = first - timedelta(days=1)
    last_month = last_month.month
    return last_month


@dataclass
class EneaResults:
    """Data container for the latest ENEA invoice and readout."""

    last_invoice_date: datetime
    last_invoice_due_date: datetime
    last_invoice_amount_pln: float
    last_invoice_unpaid_pln: float
    last_invoice_status: str
    last_readout_amount_kwh: float
    last_readout_date: datetime


class ScraperStructureError(RuntimeError):
    pass


def _extract_invoice_date(row: Tag):
    el = find_or_fail(
        row,
        {'name': 'div', 'attrs': {'class': 'datagrid-col-invoice-prognosis-date'}},
        'invoice issue date',
    )
    return parse_date(strip_div(el.get_text()))


def _extract_due_date(row: Tag):
    el = find_or_fail(
        row,
        {
            'name': 'div',
            'attrs': {'class': 'datagrid-col-invoice-prognosis-payment-date'},
        },
        'invoice due date',
    )
    return parse_date(strip_div(el.get_text()))


def _extract_invoice_value(row: Tag):
    el = find_or_fail(
        row,
        {'name': 'div', 'attrs': {'class': 'datagrid-col-invoice-prognosis-value'}},
        'invoice total value',
    )
    return parse_amount(strip_div(el.get_text()))


def _extract_invoice_unpaid(row: Tag):
    el = find_or_fail(
        row,
        {'name': 'div', 'attrs': {'class': 'datagrid-col-invoice-prognosis-payment'}},
        'invoice unpaid value',
    )
    return parse_amount(strip_div(el.get_text()))


def _extract_invoice_status(row: Tag) -> str:
    status_col = find_or_fail(
        row,
        {'name': 'div', 'attrs': {'class': 'datagrid-col-invoice-prognosis-status'}},
        'invoice status column',
    )

    texts = list(status_col.stripped_strings)

    if not texts:
        raise ScraperStructureError("ENEA HTML changed: empty invoice status")

    return " ".join(texts)


def _extract_last_invoice(soup: BeautifulSoup):
    """Extract last invoice tuple from HTML soup."""

    row = find_or_fail(
        soup,
        {'name': 'div', 'attrs': {'class': 'datagrid-row invoice-row'}},
        'invoice row',
    )

    invoice_date = _extract_invoice_date(row)
    due_date = _extract_due_date(row)
    value = _extract_invoice_value(row)
    unpaid = _extract_invoice_unpaid(row)
    status = _extract_invoice_status(row)

    return invoice_date, due_date, value, unpaid, status


def _extract_readout_date(row: Tag) -> datetime:
    el = find_or_fail(
        row,
        {
            'name': 'div',
            'attrs': {'class': 'datagrid-col-history-consumption-date'},
        },
        'readout date',
    )
    return parse_date(strip_div(el.get_text()))


def _extract_readout_value(row: Tag) -> float:
    el = find_or_fail(
        row,
        {
            'name': 'div',
            'attrs': {'class': 'datagrid-col-history-consumption-value-0'},
        },
        'readout value',
    )
    return parse_energy(strip_div(el.get_text()))


def _extract_last_readout(soup: BeautifulSoup):
    """Extract last readout value/date from HTML soup."""

    row = find_or_fail(
        soup,
        {'name': 'div', 'attrs': {'class': 'datagrid-row-content'}},
        'readout row',
    )

    readout_date = _extract_readout_date(row)
    readout_value = _extract_readout_value(row)

    return readout_value, readout_date


def parse_date(text: str):
    """Parse date in format 'dd.mm.yyyy'."""
    return datetime.strptime(text, "%d.%m.%Y")


def strip_div(text: str, nested: bool = False):
    """Normalize inner text, optionally collapsing nested newlines."""
    if not nested:
        return text.replace("\n", "")
    else:
        return text.replace("\n\n", "").replace("\n", " ")


def find_or_fail(
    soup,
    selector: dict,
    label: str,
) -> Tag:
    el = soup.find(**selector)

    if el is None:
        raise ScraperStructureError(f"ENEA HTML changed: cannot find {label}")

    if not isinstance(el, Tag):
        raise ScraperStructureError(
            f"ENEA HTML changed: {label} is not a Tag ({type(el).__name__})"
        )

    return el


class Enea(Client):
    """Session-based scraper fetching ENEA account data."""

    URL_BASE = 'https://ebok.enea.pl'
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/45.0.2454.85 Safari/537.36 '
    )
    URL_LOGIN = "/logowanie"
    URL_INVOICES = "/invoices/invoice-history"
    URL_READOUTS = "/meter/consumptionHistory"

    def __init__(self, email, password):
        """Initialize with email/password used for login."""
        self.email = email
        self.password = password
        self.userAgent = self.USER_AGENT
        self.opener = None
        self.token = ""
        self.logged_in = False

    def login(self):
        """Login to the ENEA portal and keep cookies in an opener."""
        cj = CookieJar()
        # ssl._create_default_https_context = ssl._create_unverified_context
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj)
        )
        request = urllib.request.Request(self.URL_BASE + self.URL_LOGIN)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')

        soup = BeautifulSoup(result, 'html.parser')
        token_input = find_or_fail(
            soup,
            {'name': 'input', 'attrs': {'name': 'token'}},
            'login token input',
        )
        token = token_input.get("value")

        form_parameters = {
            'email': self.email,
            'password': self.password,
            'token': token,
            'btnSubmit': "",
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
        """Collect last invoice and readout, return as `EneaResults`."""
        if self.opener is None:
            raise RuntimeError("ENEA client not logged in")
        request = urllib.request.Request(self.URL_BASE + self.URL_INVOICES)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')
        soup: BeautifulSoup = BeautifulSoup(result, 'html.parser')
        invoice_date, due_date, value, unpaid, status = _extract_last_invoice(soup)

        request = urllib.request.Request(self.URL_BASE + self.URL_READOUTS)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')
        soup = BeautifulSoup(result, 'html.parser')
        readout_value, readout_date = _extract_last_readout(soup)
        return EneaResults(
            last_invoice_date=invoice_date,
            last_invoice_due_date=due_date,
            last_invoice_amount_pln=value,
            last_invoice_unpaid_pln=unpaid,
            last_invoice_status=status,
            last_readout_amount_kwh=readout_value,
            last_readout_date=readout_date,
        )
