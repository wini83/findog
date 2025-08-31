"""Gmail SMTP adapter for sending HTML emails."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class GmailAdapter:
    """Lightweight wrapper around Gmail SMTP over SSL."""

    def __init__(self, host: str, port: int, username: str, password: str):
        """Initialize connection details and create SMTP client."""
        self.username = username
        self.password = password
        self.server = smtplib.SMTP_SSL(host, port)

    def login(self):
        """Authenticate to Gmail SMTP server."""
        self.server.ehlo()
        self.server.login(self.username, self.password)

    def send_mail(self, recipient_email: str, subject: str, content: str):
        """Send a single HTML email to the given recipient."""
        message = self._compose_message(content, recipient_email, subject)
        self.server.sendmail(self.username, recipient_email, message.as_string())

    def _compose_message(self, content, recipient_email, subject):
        """Build a MIME message with HTML body."""
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.username
        message['To'] = recipient_email
        message.attach(MIMEText(content, 'html'))
        return message

    def __del__(self):
        """Close the SMTP connection on object cleanup."""
        self.server.close()
