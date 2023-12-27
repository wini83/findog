import datetime
import urllib
from http.cookiejar import CookieJar
from typing import List

from lxml import html
from bs4 import BeautifulSoup

from datetime import date

from loguru import logger
from dataclasses import dataclass, fields

# noinspection SpellCheckingInspection
PAID = "zapłacona"
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 ' \
             'Safari/537.36 '
LOGIN_URL = "https://www.njumobile.pl/logowanie?backUrl=/mojekonto/faktury"
POST_URL = "https://www.njumobile.pl/logowanie?_DARGS=/profile-processes/login/login.jsp.portal-login-form"


def pretty_print_invoice(item: dict):
    result = "{"
    result += f'phone:{item["phone_nmb"]}; '
    result += f'invoice:{item["doc_id"]}; '
    result += f'dates:{item["issue_date"]} / {item["due_date"]}; '
    result += f'amounts:{item["amount_payable"]:.2f}PLN / {item["amount_paid"]:.2f}PLN '
    result += f'- total:{(item["amount_payable"] + item["amount_paid"]):.2f} PLN; '
    result += f'type:{item["document_type"]}; '
    result += f'status: {item["status"]}'
    if item["status"] == PAID:
        result += f' ({item["post_date"]})'
    result += "}"
    return result


# noinspection SpellCheckingInspection
def parse_row(row):
    children = row.children
    document = dict()
    for item in children:
        if item["class"][0] == 'left-right-bg':
            if item['data-title'] == "nr dokumentu":
                content = item.children.__next__()
                if content.attrs.__len__() > 0:
                    document['doc_id']: str = (content['id'].split('-')[1])
                else:
                    document['doc_id']: str = content.text
            elif item['data-title'] == "data wystawienia":
                date_issue = datetime.datetime.strptime(item.get_text(), "%d.%m.%Y").date()
                document['issue_date']: date = date_issue
            elif item['data-title'] == "termin płatności":
                date_due = datetime.datetime.strptime(item.get_text(), "%d.%m.%Y").date()
                document['due_date']: date = date_due
            elif item['data-title'] == "data zaksięgowania":
                if item.get_text() != "":
                    book_date = datetime.datetime.strptime(item.get_text(), "%d.%m.%Y").date()
                else:
                    book_date = None
                document['post_date']: date = book_date
            elif item['data-title'] == "kwota zapłacona":
                document['amount_paid']: float = float(item.get_text().replace(",", ".").split(" ")[0])
            elif item['data-title'] == "do zapłaty":
                document['amount_payable']: float = float(item.get_text().replace(",", ".").split(" ")[0])
            elif item['data-title'] == "typ dokumentu":
                document['document_type']: str = item.get_text()
            elif item['data-title'] == "za okres":
                document['accounting_period']: str = item.get_text()
            elif item['data-title'] == "status":
                document['status']: str = item.get_text()
    return document


@dataclass
class NjuInvoice:
    phone_nmb: str
    doc_id: str
    issue_date: date
    due_date: date
    post_date: date
    amount_paid: float
    amount_payable: float
    document_type: float
    accounting_period: str
    status: str

    def total(self) -> float:
        return self.amount_payable + self.amount_paid

    def pretty_print(self) -> str:
        result = "{"
        result += f'phone:{self.phone_nmb}; '
        result += f'invoice:{self.doc_id}; '
        result += f'dates:{self.issue_date} / {self.due_date}; '
        result += f'amounts:{self.amount_payable:.2f}PLN / {self.amount_paid:.2f}PLN '
        result += f'- total:{self.total():.2f} PLN; '
        result += f'type:{self.document_type}; '
        result += f'status: {self.status}'
        if self.status == PAID:
            result += f' ({self.post_date})'
        result += "}"
        return result

    def status_bool(self) -> bool:
        if self.status == PAID:
            return True
        else:
            return False


class DataClassUnpack:
    classFieldCache = {}

    @classmethod
    def instantiate(cls, class_2_instantiate, arg_dict):
        if class_2_instantiate not in cls.classFieldCache:
            cls.classFieldCache[class_2_instantiate] = {f.name for f in fields(class_2_instantiate) if f.init}

        field_set = cls.classFieldCache[class_2_instantiate]
        filtered_arg_dict = {k: v for k, v in arg_dict.items() if k in field_set}
        return class_2_instantiate(**filtered_arg_dict)


def filter_by_current_period(table: List[NjuInvoice]):
    now = datetime.datetime.now()
    filter_str = now.strftime("%m.%Y")
    list_out = list(filter(lambda x: x.accounting_period == filter_str, table))
    return list_out


def filter_not_paid(table: List[NjuInvoice]):
    list_out = list(filter(lambda x: not x.status_bool, table))
    return list_out


def print_summary(table: List[NjuInvoice], text_if_none: str = "") -> str:
    result: str = ""
    if len(table) > 0:
        total: float = 0
        ids: str = ""
        for invoice in table:
            ids += f'{invoice.doc_id};'
            total += invoice.total()
        result += f"invoice numbers: {ids}; total {total:.2f} PLN; due date: {table[0].due_date}"
    else:
        result += text_if_none
    return result


class Nju:

    def __init__(self, phone_nmb: str, password: str):
        self.userAgent = USER_AGENT
        self.opener = None
        self.logged_in: bool = False
        self.scrapped_html = None
        self.parsed = False
        self.phone_nmb = phone_nmb
        self.password = password

    def login(self):
        cj = CookieJar()
        # ssl._create_default_https_context = ssl._create_unverified_context
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        request = urllib.request.Request(LOGIN_URL)
        request.add_header('User-Agent', USER_AGENT)
        try:
            result = self.opener.open(request).read()
            result = result.decode('utf-8')

            tree = html.fromstring(result)
            authenticity_token = list(set(tree.xpath("//input[@name='_dynSessConf']/@value")))[0]

            # noinspection SpellCheckingInspection
            payload = {
                "_dyncharset": "UTF-8",
                "_dynSessConf": authenticity_token,
                "/ptk/sun/login/formhandler/LoginFormHandler.backUrl": "/mojekonto/faktury",
                "_D:/ptk/sun/login/formhandler/LoginFormHandler.backUrl": "+",
                "/ptk/sun/login/formhandler/LoginFormHandler.hashMsisdn": "",
                "_D:/ptk/sun/login/formhandler/LoginFormHandler.hashMsisdn": "+",
                "phone-input": self.phone_nmb,
                "_D:phone-input": "+",
                "password-form": self.password,
                "_D:password-form": "+",
                "login-submit": "zaloguj+się",
                "_D:login-submit": "+",
                "_DARGS": "/profile-processes/login/login.jsp.portal-login-form"}

            form_data = urllib.parse.urlencode(payload)
            request = urllib.request.Request(POST_URL)
            request.data = form_data.encode('utf-8')
            request.add_header('User-Agent', self.userAgent)
            request.add_header("Origin", "https://www.njumobile.pl")
            request.add_header("Referer", "https://www.njumobile.pl/logowanie?backUrl=/mojekonto/faktury")
            result = self.opener.open(request)
            self.logged_in = True
            result_str = result.read().decode('utf-8')
            self.scrapped_html = result_str
        except Exception as e:
            logger.exception("Nju client failed", exc_info=e)
            self.logged_in = False

    def parse_html(self):
        if not self.logged_in:
            raise ConnectionError
        bs = BeautifulSoup(self.scrapped_html, 'html.parser')
        table2 = []
        i = 1
        while True:
            raw_row = bs.find("tr", id=f"id_abc-{i}")
            if raw_row is None:
                break
            else:
                row = parse_row(raw_row)
                row["phone_nmb"] = self.phone_nmb
                row_cls = DataClassUnpack.instantiate(NjuInvoice, row)
                table2.append(row_cls)
                i = i + 1
        self.parsed = True
        return table2

    def write2file(self):
        if self.logged_in:
            file = open('nju_html.html', 'w', encoding='utf-8')
            file.write(self.scrapped_html)
            file.close()
        else:
            raise ConnectionError
