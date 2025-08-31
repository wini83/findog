"""HTTP client for iPrzedszkole to fetch receivables and costs."""

import datetime
import json
import re
from typing import NamedTuple

import requests
from bs4 import BeautifulSoup

from api_clients.client import Client


def _extract_amounts_main(bs, ident):
    """Extract amount (float) from a div with given id."""
    div = bs.find("div", id=ident)
    amount_str = div.get_text().split(' ')[0].replace(",", ".")
    return float(amount_str)


def parse_amount(amount):
    """Parse string amount with comma decimal separator to float."""
    return float(amount.replace(",", "."))


def get_last_month_int():
    """Return previous month number as int."""
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    last_month = last_month.month
    return last_month


def aspnet_tokens(html):
    """Extract ASP.NET form tokens from a response HTML page."""
    bs = BeautifulSoup(html, "html.parser")

    def v(name):
        el = bs.find("input", {"name": name})
        return el["value"] if el and el.has_attr("value") else ""

    return {
        "__VIEWSTATE": v("__VIEWSTATE"),
        "__EVENTVALIDATION": v("__EVENTVALIDATION"),
        "__VIEWSTATEGENERATOR": v("__VIEWSTATEGENERATOR"),
    }


class Receivables(NamedTuple):
    """Summary of receivables for the current period."""

    summary_to_pay: float
    summary_paid: float
    summary_overdue: float
    summary_overpayment: float
    costs_fixed: float
    costs_meal: float
    costs_additional: float


def _determine_year_start():
    """Return the school year start year (September-based)."""
    today = datetime.date.today()
    month = today.month
    year = today.year
    delta = 0
    if month < 9:
        delta = 1
    return year - delta


class Iprzedszkole(Client):
    """Session client for iPrzedszkole portal used to fetch data."""

    URL_BASE = 'https://iprzedszkole.progman.pl'
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/45.0.2454.85 Safari/537.36 '
    )
    URL_LOGIN = "/iprzedszkole/Authentication/login.aspx"
    URL_MEAL_PLAN = '/iprzedszkole/Pages/PanelRodzica/Jadlospis/Jadlospis.aspx'
    URL_RECEIVABLES_ANNUAL = (
        '/iprzedszkole/Pages/PanelRodzica/Naleznosci/'
        'ws_Naleznosci.asmx/pobierzDaneRaportRoczny'
    )
    URL_RECEIVABLES = '/iprzedszkole/Pages/PanelRodzica/Naleznosci/Naleznosci.aspx'
    URL_RECEIVABLES_DATA = (
        '/iprzedszkole/Pages/PanelRodzica/Naleznosci/'
        'ws_Naleznosci.asmx/pobierzDaneOplat'
    )
    HEADERS = {
        "User-Agent": (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/125.0.0.0 Safari/537.36'
        ),
    }

    def __init__(self, kindergarten, login, password):
        """Initialize with kindergarten name and credentials."""
        self.kindergartenName = kindergarten
        self.kindergartenLogin = login
        self.kindergartenPassword = password
        self.userAgent = self.USER_AGENT
        self.opener = None
        self.child_master_id = 0
        self.logged_in = False
        self.session = None

    def login(self):
        """Login sequence establishing a requests.Session with tokens."""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        # 1) GET login page -> cookies + tokens
        r1 = self.session.get(self.URL_BASE + self.URL_LOGIN, timeout=20)
        r1.raise_for_status()
        tokens = aspnet_tokens(r1.text)

        # 2) POST credentials + tokens (+ referer!)
        payload = {
            **tokens,
            'ctl00$cphContent$txtDatabase': self.kindergartenName,
            'ctl00$cphContent$txtLogin': self.kindergartenLogin,
            'ctl00$cphContent$txtPassword': self.kindergartenPassword,
            'ctl00$cphContent$ButtonLogin': 'Zaloguj',
        }
        r2 = self.session.post(
            self.URL_BASE + self.URL_LOGIN,
            data=payload,
            headers={"Referer": self.URL_BASE + self.URL_LOGIN},
            timeout=20,
            allow_redirects=True,
        )
        r2.raise_for_status()

        r3 = self.session.get(self.URL_BASE + self.URL_MEAL_PLAN, timeout=20)

        child_master_id = re.search(
            r'<option\s+selected="selected"\s+value="(\d+)">', r3.text
        )
        self.child_master_id = child_master_id.group(1)
        self.logged_in = True

    def get_receivables(self):
        """Fetch receivables summary and detail, return a Receivables tuple."""
        if not self.logged_in or not self.session:
            raise ConnectionError("Najpierw wywołaj login().")

        # Wejście na stronę należności (dobry 'Referer'/kontekst dla ASMX)
        r0 = self.session.get(self.URL_BASE + self.URL_RECEIVABLES, timeout=20)
        r0.raise_for_status()

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.URL_BASE + self.URL_RECEIVABLES,
        }

        # --- 1) Raport roczny -> wyciąg sum dla bieżącego miesiąca ---
        year_start = _determine_year_start()
        payload_annual = {
            "args": {
                "dzieckoId": int(self.child_master_id),
                "rokStart": str(year_start),
                "listViewName": "Szczegoly",
            }
        }
        r1 = self.session.post(
            self.URL_BASE + self.URL_RECEIVABLES_ANNUAL,
            data=json.dumps(payload_annual),
            headers=headers,
            timeout=20,
        )
        r1.raise_for_status()
        data1 = r1.json()  # klasycznie 'd' od ASP.NET AJAX
        periods = data1["d"]["ListData"]

        # wybierz rekord dla obecnego miesiąca/roku
        today = datetime.date.today()
        month = today.month
        year = today.year
        amounts_summary = next(
            (
                p
                for p in periods
                if int(p.get("Rok", 0)) == year and int(p.get("Miesiac", 0)) == month
            ),
            None,
        )
        if amounts_summary is None:
            # fallback: weź najnowszy dostępny okres (gdy brak bieżącego)
            amounts_summary = max(
                periods, key=lambda p: (int(p.get("Rok", 0)), int(p.get("Miesiac", 0)))
            )

        summary_to_pay = amounts_summary["DoZaplaty"]
        summary_paid = amounts_summary["Zaplacono"]
        summary_overdue = amounts_summary["Zaleglosc"]
        summary_overpayment = amounts_summary["Nadplata"]

        # --- 2) Szczegóły opłat (stała/posiłki/dodatkowe) ---
        payload_details = {
            "idDziecko": str(self.child_master_id)
        }  # ten endpoint nie używa 'args'
        r2 = self.session.post(
            self.URL_BASE + self.URL_RECEIVABLES_DATA,
            data=json.dumps(payload_details),
            headers=headers,
            timeout=20,
        )
        r2.raise_for_status()
        data2 = r2.json()
        receivables = data2["d"]["ListK"]

        costs_fixed = 0.0
        costs_meal = 0.0
        costs_additional = 0.0

        for rec in receivables:
            kind = rec.get("RodzajOplaty")
            if kind == 0:
                costs_fixed = rec["Kwota"]
            elif kind == 1:
                costs_additional = rec["Kwota"]
            elif kind == 2:
                costs_meal = rec["Kwota"]

        return Receivables(
            summary_to_pay=summary_to_pay,
            summary_paid=summary_paid,
            summary_overdue=summary_overdue,
            summary_overpayment=summary_overpayment,
            costs_fixed=costs_fixed,
            costs_meal=costs_meal,
            costs_additional=costs_additional,
        )
