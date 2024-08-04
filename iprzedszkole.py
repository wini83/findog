import datetime
import json
import re
import ssl
import urllib.request
from http.cookiejar import CookieJar
from typing import NamedTuple

from bs4 import BeautifulSoup

from api_clients.client import Client


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
    summary_to_pay: float
    summary_paid: float
    summary_overdue: float
    summary_overpayment: float
    costs_fixed: float
    costs_meal: float
    costs_additional: float


def _determine_year_start():
    today = datetime.date.today()
    month = today.month
    year = today.year
    delta = 0
    if month < 9:
        delta = 1
    return year - delta


class Iprzedszkole(Client):
    URL_BASE = 'https://iprzedszkole.progman.pl'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 ' \
                 'Safari/537.36 '
    URL_LOGIN = "/iprzedszkole/Authentication/login.aspx"
    URL_MEAL_PLAN = '/iprzedszkole/Pages/PanelRodzica/Jadlospis/Jadlospis.aspx'
    URL_RECEIVABLES_ANNUAL = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/ws_Naleznosci.asmx/pobierzDaneRaportRoczny'
    URL_RECEIVABLES = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/Naleznosci.aspx'
    URL_RECEIVABLES_DATA = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/ws_Naleznosci.asmx/pobierzDaneOplat'

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

        strings = f'{{"args": {{"dzieckoId": {self.child_master_id}, "rokStart": "{_determine_year_start()}", ' \
                  f'"listViewName": "Szczegoly"}}}} '

        request = urllib.request.Request(
            self.URL_BASE + self.URL_RECEIVABLES_ANNUAL)
        request.data = strings.encode('utf-8')
        request.add_header('Content-Type', 'application/json; charset=utf-8')
        result = self.opener.open(request).read()

        result = json.loads(result)
        periods = result["d"]["ListData"]
        amounts_summary = None
        today = datetime.date.today()
        month = today.month
        year = today.year
        for period in periods:
            if period['Rok'] == year and period["Miesiac"] == month:
                amounts_summary = period
        if amounts_summary is None:
            raise ValueError()
        summary_to_pay = amounts_summary["DoZaplaty"]
        summary_paid = amounts_summary["Zaplacono"]
        summary_overdue = amounts_summary["Zaleglosc"]
        summary_overpayment = amounts_summary["Nadplata"]

        strings = f'{{"idDziecko": "{self.child_master_id}"}} '

        request2 = urllib.request.Request(
            self.URL_BASE + self.URL_RECEIVABLES_DATA)
        request2.data = strings.encode('utf-8')
        request2.add_header('Content-Type', 'application/json; charset=utf-8')
        result2 = self.opener.open(request2).read()

        result2 = json.loads(result2)

        receivables = result2["d"]["ListK"]

        costs_fixed = 0
        costs_meal = 0
        costs_additional = 0

        for receivable in receivables:
            if receivable["RodzajOplaty"] == 0:
                costs_fixed = receivable["Kwota"]
            elif receivable["RodzajOplaty"] == 1:
                costs_additional = receivable["Kwota"]
            elif receivable["RodzajOplaty"] == 2:
                costs_meal = receivable["Kwota"]

        return Receivables(
            summary_to_pay=summary_to_pay,
            summary_paid=summary_paid,
            summary_overdue=summary_overdue,
            summary_overpayment=summary_overpayment,
            costs_fixed=costs_fixed,
            costs_meal=costs_meal,
            costs_additional=costs_additional)
