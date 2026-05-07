import smtplib
from typing import TYPE_CHECKING

import pytest

from minizen.config.models import EmailConfig
from minizen.exceptions import EmailError
from minizen.providers.email.smtp import EmailProvider, is_transient_smtp

if TYPE_CHECKING:
    from email.mime.multipart import MIMEMultipart

    from pytest_mock import MockerFixture


def test_send_connects_and_sends_message(mocker: MockerFixture) -> None:
    # arrange
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp = mock_smtp_cls.return_value.__enter__.return_value
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act
    provider.send(subject="Daily Digest", html="<h1>Hello</h1>")

    # assert
    mock_smtp_cls.assert_called_once_with(host="smtp.example.com", port=587)
    mock_smtp.starttls.assert_called_once_with()
    mock_smtp.login.assert_called_once_with(user="user", password="pass")
    sent_msg: MIMEMultipart = mock_smtp.send_message.call_args[0][0]
    mock_smtp.send_message.assert_called_once_with(sent_msg)


def test_send_attaches_plain_text_when_provided(mocker: MockerFixture) -> None:
    # arrange
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp = mock_smtp_cls.return_value.__enter__.return_value
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act
    provider.send(subject="Daily Digest", html="<h1>Hello</h1>", plain_text="Hello")

    # assert
    sent_msg = mock_smtp.send_message.call_args[0][0]
    payloads = sent_msg.get_payload()
    assert any(p.get_content_type() == "text/plain" for p in payloads)
    assert any(p.get_content_type() == "text/html" for p in payloads)


def test_send_message_has_correct_headers(mocker: MockerFixture) -> None:
    # arrange
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp = mock_smtp_cls.return_value.__enter__.return_value
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act
    provider.send(subject="Daily Digest", html="<h1>Hello</h1>")

    # assert
    sent_msg: MIMEMultipart = mock_smtp.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "Daily Digest"
    assert sent_msg["From"] == "from@example.com"
    assert sent_msg["To"] == "to@example.com"


def test_send_raises_email_error_on_smtp_exception(mocker: MockerFixture) -> None:
    # arrange
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp_cls.return_value.__enter__.return_value.starttls.side_effect = (
        smtplib.SMTPException("Connection failed")
    )
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act / assert
    with pytest.raises(EmailError, match="Email delivery failed"):
        provider.send(subject="Test", html="<p>Hello</p>")


def test_send_raises_email_error_on_os_error(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp_cls.side_effect = OSError("Network unreachable")
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act / assert
    with pytest.raises(EmailError, match="Email delivery failed"):
        provider.send(subject="Test", html="<p>Hello</p>")


def test_is_transient_smtp_returns_true_for_os_error() -> None:
    assert is_transient_smtp(exc=OSError("network unreachable")) is True


def test_is_transient_smtp_returns_true_for_connect_error() -> None:
    assert (
        is_transient_smtp(exc=smtplib.SMTPConnectError(421, b"Service unavailable"))
        is True
    )


def test_is_transient_smtp_returns_true_for_server_disconnected() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPServerDisconnected("disconnected")) is True


def test_is_transient_smtp_returns_false_for_auth_error() -> None:
    assert (
        is_transient_smtp(exc=smtplib.SMTPAuthenticationError(535, b"Bad credentials"))
        is False
    )


def test_is_transient_smtp_returns_false_for_recipients_refused() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPRecipientsRefused({})) is False


def test_is_transient_smtp_returns_false_for_base_smtp_exception() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPException("generic")) is False


def test_send_retries_on_transient_error_then_succeeds(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp_cls.side_effect = [
        OSError("Connection refused"),
        mock_smtp_cls.return_value,
    ]
    mock_smtp = mock_smtp_cls.return_value.__enter__.return_value
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act
    provider.send(subject="Test", html="<p>Hello</p>")

    # assert
    assert mock_smtp_cls.call_count == 2
    mock_smtp.send_message.assert_called_once_with(
        mock_smtp.send_message.call_args[0][0]
    )


def test_send_raises_email_error_after_exhausting_retries(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp_cls.side_effect = OSError("Network unreachable")
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )
    provider = EmailProvider(config=config)

    # act / assert
    with pytest.raises(EmailError, match="Email delivery failed"):
        provider.send(subject="Test", html="<p>Hello</p>")
    assert mock_smtp_cls.call_count == 3
