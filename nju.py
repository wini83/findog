import datetime
import ssl
import urllib
from http.cookiejar import CookieJar
from typing import List

from lxml import html
from bs4 import BeautifulSoup

from datetime import date


def parse_row(row):
    children = row.children
    document = dict()
    for item in children:
        if item["class"][0] == 'left-right-bg':
            if item['data-title'] == "nr dokumentu":
                content = item.children.__next__()
                if content.attrs.__len__() > 0:
                    document['doc-id']: str = (content['id'].split('-')[1])
                else:
                    document['doc-id']: str = content.text
            elif item['data-title'] == "data wystawienia":
                date_issue = datetime.datetime.strptime(item.get_text(), "%d.%m.%Y").date()
                document['issue date']: date = date_issue
            elif item['data-title'] == "termin płatności":
                date_due = datetime.datetime.strptime(item.get_text(), "%d.%m.%Y").date()
                document['due date']: date = date_due
            elif item['data-title'] == "data zaksięgowania":
                if item.get_text() != "":
                    book_date = datetime.datetime.strptime(item.get_text(), "%d.%m.%Y").date()
                else:
                    book_date = None
                document['post date']: date = book_date
            elif item['data-title'] == "kwota zapłacona":
                document['amount paid']: float = float(item.get_text().replace(",", ".").split(" ")[0])
            elif item['data-title'] == "do zapłaty":
                document['amount payable']: float = float(item.get_text().replace(",", ".").split(" ")[0])
            elif item['data-title'] == "typ dokumentu":
                document['document type']: str = item.get_text()
            elif item['data-title'] == "za okres":
                document['accounting period']: str = item.get_text()
            elif item['data-title'] == "status":
                document['status']: str = item.get_text()
    return document


def filter_by_current_period(table: List[dict]):
    now = datetime.datetime.now()
    fltr_str = now.strftime("%m.%Y")
    list_out = list(filter(lambda x: x['accounting period'] == fltr_str, table))
    return list_out


def filter_not_paid(table: List[dict]):
    list_out = list(filter(lambda x: x['status'] != "zapłacona", table))
    return list_out


def preety_print(item: dict):
    result = "{"
    result += f'phone:{item["phone_nmb"]}; '
    result += f'invoice:{item["doc-id"]}; '
    result += f'dates:{item["issue date"]} / {item["due date"]}; '
    result += f'amounts:{item["amount payable"]:.2f}PLN / {item["amount paid"]:.2f}PLN - total:{(item["amount payable"] + item["amount paid"]):.2f} PLN; '
    result += f'type:{item["document type"]}; '
    result += f'status: {item["status"]}'
    if item["status"] == "zapłacona":
        result += f' ({item["post date"]})'
    result += "}"
    return result


class Nju():
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 ' \
                 'Safari/537.36 '
    LOGIN_URL = "https://www.njumobile.pl/logowanie?backUrl=/mojekonto/faktury"

    def __init__(self, phone_nmb: str, password: str):
        self.userAgent = self.USER_AGENT
        self.opener = None
        self.logged_in: bool = False
        self.scrapped_html = None
        self.parsed = False
        self.phone_nmb = phone_nmb
        self.password = password

    def login(self):
        cj = CookieJar()
        ssl._create_default_https_context = ssl._create_unverified_context
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        request = urllib.request.Request(self.LOGIN_URL)
        request.add_header('User-Agent', self.USER_AGENT)
        try:
            result = self.opener.open(request).read()
            result = result.decode('utf-8')

            tree = html.fromstring(result)
            authenticity_token = list(set(tree.xpath("//input[@name='_dynSessConf']/@value")))[0]

            post_url = "https://www.njumobile.pl/logowanie?_DARGS=/profile-processes/login/login.jsp.portal-login-form"

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
            request = urllib.request.Request(post_url)
            request.data = form_data.encode('utf-8')
            request.add_header('User-Agent', self.userAgent)
            request.add_header("Origin", "https://www.njumobile.pl")
            request.add_header("Referer", "https://www.njumobile.pl/logowanie?backUrl=/mojekonto/faktury")
            result = self.opener.open(request)
            self.logged_in = True
            result_str = result.read().decode('utf-8')
            self.scrapped_html = result_str
        except:
            self.logged_in = False

    def parse_html(self):
        if not self.logged_in:
            raise ConnectionError
        bs = BeautifulSoup(self.scrapped_html, 'html.parser')
        table = []
        i = 1
        while True:
            raw_row = bs.find("tr", id=f"id_abc-{i}")
            if raw_row is None:
                break
            else:
                row = parse_row(raw_row)
                row["phone_nmb"] = self.phone_nmb
                table.append(row)
                i = i + 1
        self.parsed = True
        return table

    def write2file(self, payload):
        if self.logged_in:
            file = open('wynik.html', 'w', encoding='utf-8')
            file.write(self.scrapped_html)
            file.close()
        else:
            raise ConnectionError
