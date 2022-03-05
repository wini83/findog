import datetime
import json
import ssl
import urllib.request
from http.cookiejar import CookieJar
from typing import NamedTuple

from bs4 import BeautifulSoup

from Client import Client


def _extract_amounts_main(bs):
    span = bs.find('span', {'class': 'h1 value-to-pay'})
    amount_str = span.get_text().strip().rstrip("zł").strip().replace(",",".")
    return float(amount_str)


def parse_amount(amount):
    return float(amount.replace(",", "."))


def get_last_month_int():
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    last_month = last_month.month
    return last_month


class Receivables(NamedTuple):
    summary_to_pay: float
    summary_paid: float
    summary_overdue: float
    summary_overpayment: float
    costs_fixed: float
    costs_meal: float
    costs_additional: float


class Enea(Client):
    URL_BASE = 'https://ebok.enea.pl'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 ' \
                 'Safari/537.36 '
    URL_LOGIN = "/logowanie"
    URL_MEAL_PLAN = '/iprzedszkole/Pages/PanelRodzica/Jadlospis/Jadlospis.aspx'
    URL_RECEIVABLES_ANNUAL = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/ws_Naleznosci.asmx/pobierzDaneRaportRoczny'
    URL_RECEIVABLES = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/Naleznosci.aspx'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.userAgent = self.USER_AGENT
        self.opener = None
        self.token = ""
        self.logged_in = False

    def login(self):
        cj = CookieJar()
        ssl._create_default_https_context = ssl._create_unverified_context
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
        request = urllib.request.Request(result.url)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')
        soup = BeautifulSoup(result, 'html.parser')
        amount = _extract_amounts_main(soup)
        status = soup.find('span', {'class': 'text-info-box'}).get_text().strip()
        self.logged_in = True
        return amount, status
