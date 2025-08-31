"""Pushover client for push notifications."""

import http.client
import urllib

from api_clients.client import Client


class Pushover(Client):
    """Simple Pushover API wrapper to send messages and errors."""

    def __init__(self, apikey: str, user: str):
        """Store API credentials for later requests."""
        self.apikey = apikey
        self.user = user

    def login(self):
        """Pushover does not require an explicit login."""
        pass

    def notify(self, message: str):
        """Send a notification message via Pushover."""
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request(
            "POST",
            "/1/messages.json",
            urllib.parse.urlencode(
                {
                    "token": self.apikey,
                    "user": self.user,
                    "message": message,
                }
            ),
            {"Content-type": "application/x-www-form-urlencoded"},
        )
        conn.getresponse()

    def error(self, message):
        """Send an error-prefixed notification."""
        self.notify(f'ERROR:{message}')
