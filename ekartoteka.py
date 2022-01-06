import codecs
import json
from base64 import b64decode
from datetime import datetime

from json import JSONDecodeError
from urllib import request
from urllib.error import URLError

from Client import Client
from payment_book import PaymentBook


def seconds_from_epoch() -> int:
    from_epoch = datetime.now().timestamp().__floor__()
    return int(from_epoch)


class Ekartoteka(Client):
    URL_SETTLEMENTS = "https://e-kartoteka.pl/api/rozrachunki/konta/?id_a_do={}&id_kli={}&rok={}"
    URL_TOKEN = "https://e-kartoteka.pl/api/api-token-auth/"
    URL_ME = "https://e-kartoteka.pl/api/uzytkownicy/uzytkownicy/me/"
    URL_PREMISES = "https://e-kartoteka.pl/api/oplatymiesieczne/lokale/?id_a_do={}&id_kli={}"
    URL_MOTHLY_FEES_SUM = "https://e-kartoteka.pl/api/oplatymiesieczne/oplatymiesiecznenalokale/suma/?id_a_do={" \
                          "}&id_kli={} "
    token: str
    _creditentials = None
    user_full_name: str = None
    user_email: str = None
    user_id: int
    client_id: int
    token_expire: int
    _payment_book: PaymentBook = None

    def __init__(self, creditentials, payment_book: PaymentBook):
        self._payment_book = payment_book
        self._creditentials = creditentials

    def _get_token(self):
        headers = {"Content-type": "application/json"}
        payload = json.dumps(self._creditentials)
        req = request.Request(self.URL_TOKEN, payload.encode(), headers)
        try:
            response = request.urlopen(req)
            reader = codecs.getreader("utf-8")
            # Parse Json
            data = json.load(reader(response))
            self.token = data["token"]
            return True
        except URLError as urle:
            print(f'{urle.reason}')
            return False

        except JSONDecodeError as e:
            print(f'{e.msg}')
            return False

    def _decode_token(self):
        stra = self.token.split(".")[1]
        stra += '=' * (-len(stra) % 4)  # restore stripped '='s
        payload = b64decode(stra).decode("utf-8")
        json_hr = json.loads(payload)
        id_cli = json_hr["username"].split("_")[0]
        id_cli = int(id_cli)
        self.client_id = id_cli
        exp = int(json_hr["exp"])
        self.token_expire = exp

    def _get_me(self):
        if self.token is None:
            return False
        headers = {"Content-type": "application/json", 'Authorization': f'Bearer {self.token}'}
        req = request.Request(self.URL_ME, headers=headers)
        try:
            response = request.urlopen(req)
            reader = codecs.getreader("utf-8")
            # Parse Json
            data = json.load(reader(response))
            self.user_full_name = data["Nazwa"]
            self.user_email = data["Email"]
            self.user_id = data["DaneKsiegowe"][0]
            return True
        except URLError as urle:
            print(f'{urle.reason}')
            return False
        except JSONDecodeError as e:
            print(f'{e.msg}')
            return False
        except KeyError:
            print("Wrong key")
            return False

    def login(self):
        self._get_token()
        self._get_me()
        self._decode_token()

    def get_settlements(self, year: int):
        if self.token is None:
            return False, "Not initialized"
        headers = {"Content-type": "application/json", 'Authorization': f'Bearer {self.token}'}
        url = self.URL_SETTLEMENTS.format(self.user_id, self.client_id, year)
        req = request.Request(url, headers=headers)
        try:
            response = request.urlopen(req)
            reader = codecs.getreader("utf-8")
            # Parse Json
            data = json.load(reader(response))
            return True, data
        except URLError:
            return False, "Network Problem"
        except JSONDecodeError:
            return False, "Response is not Json;"
        except ValueError:
            return False, "Wrong response structure"

    def get_settlements_sum(self, year: int):
        res, data = self.get_settlements(year=year)
        if not res:
            return False, None
        else:
            positions = data["results"]
            # print(positions)
            balance = 0.0
            for position in positions:
                balance += position["Wn"] - position["Ma"]
            return True, balance

    def get_premises_data(self):
        if self.token is None:
            return False, "Not initialized"
        headers = {"Content-type": "application/json", 'Authorization': f'Bearer {self.token}'}
        url = self.URL_PREMISES.format(self.user_id, self.client_id)
        req = request.Request(url, headers=headers)
        try:
            response = request.urlopen(req)
            reader = codecs.getreader("utf-8")
            # Parse Json
            data = json.load(reader(response))
            print(data)
            return True, data
        except URLError:
            return False, "Network Problem"
        except JSONDecodeError:
            return False, "Response is not Json;"
        except ValueError:
            return False, "Wrong response structure"

    def get_curret_fees_sum(self):
        if self.token is None:
            return False, "Not initialized"
        headers = {"Content-type": "application/json", 'Authorization': f'Bearer {self.token}'}
        url = self.URL_MOTHLY_FEES_SUM.format(self.user_id, self.client_id)
        req = request.Request(url, headers=headers)
        try:
            response = request.urlopen(req)
            reader = codecs.getreader("utf-8")
            # Parse Json
            data = json.load(reader(response))
            return data[0]["Brutto"]
        except URLError:
            return False, "Network Problem"
        except JSONDecodeError:
            return False, "Response is not Json;"
        except ValueError:
            return False, "Wrong response structure"

    def update_payment_book(self, sheet_name: str, category_name: str):
        # TODO: not initialized
        apartment_fee = self.get_curret_fees_sum()
        res_setl, delta = self.get_settlements_sum(datetime.now().year)

        if res_setl and delta is not None:
            if delta > 0:
                paid = False
            else:
                paid = True
        else:
            paid = None
        now = datetime.now()
        # TODO: recognition of Ekartoteka update
        if now.day < 8:
            paid = None
        self._payment_book.update_current_payment(sheet_name, category_name, amount=apartment_fee, paid=paid)
        return apartment_fee, delta
