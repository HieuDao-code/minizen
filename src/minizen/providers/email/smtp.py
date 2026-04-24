import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from minizen.config.models import EmailConfig


class EmailProvider:
    def __init__(self, *, config: EmailConfig) -> None:
        self._config = config

    def send(self, *, subject: str, html: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._config.from_addr
        msg["To"] = self._config.to_addr
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(
            host=self._config.smtp_host, port=self._config.smtp_port
        ) as server:
            server.starttls()
            server.login(user=self._config.username, password=self._config.password)
            server.send_message(msg)
