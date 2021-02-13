import http.client
import string
import urllib


class Pushover:
    def __init__(self, apikey: string, user: string):
        self.apikey = apikey
        self.user = user

    def notify(self, message: string):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": self.apikey,
                         "user": self.user,
                         "message": message,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()
