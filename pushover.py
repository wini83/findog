import http.client
import urllib

from api_clients.Client import Client


class Pushover(Client):
    def __init__(self, apikey: str, user: str):
        self.apikey = apikey
        self.user = user

    def login(self):
        pass

    def notify(self, message: str):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": self.apikey,
                         "user": self.user,
                         "message": message,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()

    def error(self, message):
        self.notify(f'ERROR:{message}')
