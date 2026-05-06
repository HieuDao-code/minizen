"""SMTP email sender for delivering multipart HTML/plain-text digest emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from minizen.config.models import EmailConfig

logger = logging.getLogger(__name__)


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
            smtplib.SMTPAuthenticationError: If SMTP credentials are rejected by the server.
            smtplib.SMTPRecipientsRefused: If all recipient addresses are refused.
            smtplib.SMTPException: If any other SMTP-level error occurs during sending.
            OSError: If a network error occurs connecting to the SMTP server.
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
            with smtplib.SMTP(
                host=self._config.smtp_host, port=self._config.smtp_port
            ) as server:
                server.starttls()
                server.login(user=self._config.username, password=self._config.password)
                server.send_message(msg)
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed for %r on %s:%d",
                self._config.username,
                self._config.smtp_host,
                self._config.smtp_port,
            )
            raise
        except smtplib.SMTPRecipientsRefused as exc:
            logger.error(
                "SMTP recipients refused on %s:%d: %s",
                self._config.smtp_host,
                self._config.smtp_port,
                list(exc.recipients),
            )
            raise
        except smtplib.SMTPException as exc:
            logger.error(
                "SMTP error sending to %s via %s:%d: %s",
                self._config.to_addr,
                self._config.smtp_host,
                self._config.smtp_port,
                exc,
            )
            raise
        except OSError as exc:
            logger.error(
                "Network error connecting to SMTP server %s:%d: %s",
                self._config.smtp_host,
                self._config.smtp_port,
                exc,
            )
            raise
