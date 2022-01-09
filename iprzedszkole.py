from http.cookiejar import CookieJar

import urllib.request
import re
import json
import datetime
from typing import NamedTuple

import ssl
import certifi

from bs4 import BeautifulSoup

from Client import Client


def _extract_amounts_main(bs, ident):
    div = bs.find("div", id=ident)
    amount_str = div.get_text().split(' ')[0].replace(",", ".")
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
    amount_to_pay: float
    amount_paid: float
    amount_overdue: float
    amount_overpayment: float
    summary_to_pay: float
    summary_paid: float
    summary_overdue: float
    summary_overpayment: float
    costs_fixed: float
    costs_meal: float
    costs_additional: float


class Iprzedszkole(Client):
    URL_BASE = 'https://iprzedszkole.progman.pl'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 ' \
                 'Safari/537.36 '
    URL_LOGIN = "/iprzedszkole/Authentication/Login.aspx"
    URL_MEAL_PLAN = '/iprzedszkole/Pages/PanelRodzica/Jadlospis/Jadlospis.aspx'
    URL_RECEIVABLES_ANNUAL = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/ws_Naleznosci.asmx/pobierzDaneRaportRoczny'
    URL_RECEIVABLES = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/Naleznosci.aspx'

    def __init__(self, kindergarten, login, password):
        self.kindergartenName = kindergarten
        self.kindergartenLogin = login
        self.kindergartenPassword = password
        self.userAgent = self.USER_AGENT
        self.opener = None
        self.child_master_id = 0
        self.logged_in = False

    def login(self):
        cj = CookieJar()
        ssl._create_default_https_context = ssl._create_unverified_context
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        request = urllib.request.Request(self.URL_BASE + self.URL_LOGIN)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')

        view_state = re.search(
            '<input\s+type="hidden"\s+name="__VIEWSTATE"\s+id="__VIEWSTATE"\s+value="([/+=\w]+)"\s+/>', result)
        view_state = view_state.group(1)

        view_state_generator = re.search(
            '<input\s+type="hidden"\s+name="__VIEWSTATEGENERATOR"\s+id="__VIEWSTATEGENERATOR"\s+value="([/+=\w]+)"\s+/>',
            result)
        view_state_generator = view_state_generator.group(1)

        event_validation = re.search(
            '<input\s+type="hidden"\s+name="__EVENTVALIDATION"\s+id="__EVENTVALIDATION"\s+value="([/+=\w]+)"\s+/>',
            result)
        event_validation = event_validation.group(1)

        form_parameters = {'__VIEWSTATE': view_state,
                           '__VIEWSTATEGENERATOR': view_state_generator,
                           '__EVENTVALIDATION': event_validation,
                           'ctl00$cphContent$txtDatabase': self.kindergartenName,
                           'ctl00$cphContent$txtLogin': self.kindergartenLogin,
                           'ctl00$cphContent$txtPassword': self.kindergartenPassword,
                           'ctl00$cphContent$Button1': 'Zaloguj'
                           }

        form_data = urllib.parse.urlencode(form_parameters)

        request = urllib.request.Request(self.URL_BASE + self.URL_LOGIN)
        request.data = form_data.encode('utf-8')
        request.add_header('User-Agent', self.userAgent)
        self.opener.open(request)

        request = urllib.request.Request(self.URL_BASE + self.URL_MEAL_PLAN)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')

        child_master_id = re.search('<option\s+selected="selected"\s+value="(\d+)">', result)
        self.child_master_id = child_master_id.group(1)
        self.logged_in = True

    def get_receivables(self):
        if not self.logged_in:
            raise ConnectionError
        request_payload_2 = "{idDziecko: %s, rokStart: 2021}" % self.child_master_id

        request = urllib.request.Request(
            self.URL_BASE + self.URL_RECEIVABLES_ANNUAL)
        request.data = request_payload_2.encode('utf-8')
        request.add_header('Content-Type', 'application/json; charset=utf-8')
        result = self.opener.open(request).read()

        zbigniew = json.loads(result)

        kwoty = zbigniew["d"]["kwoty"]

        summary = zbigniew["d"]["razem"]

        amounts_current = kwoty[get_last_month_int().__str__()]

        amount_to_pay = parse_amount(amounts_current["kw1"])
        amount_paid = parse_amount(amounts_current["kw2"])
        amount_overdue = parse_amount(amounts_current["kw3"])
        amount_overpayment = parse_amount(amounts_current["kw4"])

        summary_to_pay = parse_amount(summary["kw1"])
        summary_paid = parse_amount(summary["kw2"])
        summary_overdue = parse_amount(summary["kw3"])
        summary_overpayment = parse_amount(summary["kw4"])

        request = urllib.request.Request(self.URL_BASE + self.URL_RECEIVABLES)
        request.add_header('User-Agent', self.userAgent)
        result = self.opener.open(request).read()
        result = result.decode('utf-8')
        bs = BeautifulSoup(result, 'html.parser')

        costs_fixed = _extract_amounts_main(bs, "ctl00_ContentPlaceHolder1_kwotaStale")
        costs_meal = _extract_amounts_main(bs, "ctl00_ContentPlaceHolder1_kwotaPosilki")
        costs_additional = _extract_amounts_main(bs, "ctl00_ContentPlaceHolder1_kwotaDodatkowe")

        return Receivables(
            amount_to_pay=amount_to_pay,
            amount_paid=amount_paid,
            amount_overdue=amount_overdue,
            amount_overpayment=amount_overpayment,
            summary_to_pay=summary_to_pay,
            summary_paid=summary_paid,
            summary_overdue=summary_overdue,
            summary_overpayment=summary_overpayment,
            costs_fixed=costs_fixed,
            costs_meal=costs_meal,
            costs_additional=costs_additional)
