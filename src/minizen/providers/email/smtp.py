import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from minizen.config.models import EmailConfig


class EmailProvider:
    """SMTP email sender that delivers multipart HTML/plain-text messages."""

    def __init__(self, *, config: EmailConfig) -> None:
        """Initialise the provider with the given email configuration.

        Args:
            config: SMTP connection and addressing settings.
        """
        self._config = config

    def send(self, *, subject: str, html: str, plain_text: str = "") -> None:
        """Send an email with an HTML body and an optional plain-text fallback.

        Args:
            subject: Email subject line.
            html: HTML body of the message.
            plain_text: Optional plain-text alternative; omitted if empty.
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._config.from_addr
        msg["To"] = self._config.to_addr
        if plain_text:
            msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(
            host=self._config.smtp_host, port=self._config.smtp_port
        ) as server:
            server.starttls()
            server.login(user=self._config.username, password=self._config.password)
            server.send_message(msg)
