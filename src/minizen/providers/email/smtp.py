"""SMTP email sender for delivering multipart HTML/plain-text digest emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from minizen.exceptions import EmailError
from minizen.retry import retry_transient

if TYPE_CHECKING:
    from minizen.config.models import EmailConfig

logger = logging.getLogger(__name__)


def is_transient_smtp(exc: BaseException) -> bool:
    """Return True if exc is a transient SMTP error that warrants a retry.

    Args:
        exc: The exception to classify.

    Returns:
        True for ``OSError``, ``SMTPConnectError``, and ``SMTPServerDisconnected``;
        False for auth failures, refused recipients, and all other exceptions.
    """
    if isinstance(exc, smtplib.SMTPException):
        return isinstance(
            exc, (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected)
        )
    return isinstance(exc, OSError)


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

        Raises:
            EmailError: If the SMTP connection or send fails after all retries.
        """
        logger.debug(
            "Sending email: subject=%r, to=%s, smtp=%s:%d",
            subject,
            self._config.to_addr,
            self._config.smtp_host,
            self._config.smtp_port,
        )
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._config.from_addr
        msg["To"] = self._config.to_addr
        if plain_text:
            msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            self._deliver(msg=msg)
        except (smtplib.SMTPException, OSError) as exc:
            err_msg = f"Email delivery failed: {exc}"
            raise EmailError(err_msg) from exc

    @retry_transient(is_transient_smtp)
    def _deliver(self, *, msg: MIMEMultipart) -> None:
        """Deliver a MIME message over SMTP, retrying on transient errors.

        Args:
            msg: The fully-constructed MIME message to send.

        Raises:
            smtplib.SMTPConnectError: If the server cannot be reached (retried).
            smtplib.SMTPServerDisconnected: If the connection drops (retried).
            smtplib.SMTPAuthenticationError: If credentials are rejected (not retried).
            smtplib.SMTPRecipientsRefused: If recipients are rejected (not retried).
            OSError: On network-level failures (retried).
        """
        with smtplib.SMTP(
            host=self._config.smtp_host, port=self._config.smtp_port
        ) as server:
            server.starttls()
            server.login(user=self._config.username, password=self._config.password)
            server.send_message(msg)
