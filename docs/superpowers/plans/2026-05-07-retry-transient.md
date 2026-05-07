# Retry on Transient Failure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automatic retry with exponential backoff and jitter for transient network errors in `MinifluxProvider` and `EmailProvider` using tenacity.

**Architecture:** A `retry_transient(is_transient)` factory in `src/minizen/retry.py` wraps tenacity's `retry` decorator with project-standard settings (3 attempts, exponential jitter 1s–30s, WARNING log before sleep, reraise on exhaustion). Each provider defines its own public `is_transient_*` predicate and applies the decorator to a private inner method; the public method handles exception wrapping to `MinifluxError`/`EmailError` as before.

**Tech Stack:** `tenacity` (new dependency), `pytest-mock` (existing)

---

### Task 1: Add tenacity dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add tenacity to pyproject.toml**

In the `dependencies` list in `pyproject.toml`, add:
```toml
"tenacity>=9.0.0,<10.0.0",
```

- [ ] **Step 2: Update the lock file**

```bash
uv lock
```
Expected: lock file updated with tenacity and its transitive dependencies, no errors.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add tenacity dependency for retry logic"
```

---

### Task 2: Create retry module

**Files:**
- Create: `src/minizen/retry.py`
- Create: `tests/test_retry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_retry.py`:
```python
"""Tests for the retry_transient decorator factory."""

from typing import TYPE_CHECKING

import pytest

from minizen.retry import retry_transient

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_retry_transient_returns_value_on_first_success() -> None:
    @retry_transient(lambda _: True)
    def fn() -> str:
        return "ok"

    assert fn() == "ok"


def test_retry_transient_retries_on_transient_error(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    call_count = 0

    @retry_transient(lambda exc: isinstance(exc, ValueError))
    def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient")
        return "ok"

    # act
    result = fn()

    # assert
    assert result == "ok"
    assert call_count == 3


def test_retry_transient_does_not_retry_permanent_error(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    call_count = 0

    @retry_transient(lambda exc: isinstance(exc, ValueError))
    def fn() -> None:
        nonlocal call_count
        call_count += 1
        raise TypeError("permanent")

    # act / assert
    with pytest.raises(TypeError, match="permanent"):
        fn()
    assert call_count == 1


def test_retry_transient_reraises_after_exhaustion(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    call_count = 0

    @retry_transient(lambda exc: isinstance(exc, ValueError))
    def fn() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("transient")

    # act / assert
    with pytest.raises(ValueError, match="transient"):
        fn()
    assert call_count == 3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_retry.py -v
```
Expected: `ImportError` — `minizen.retry` does not exist yet.

- [ ] **Step 3: Create `src/minizen/retry.py`**

```python
"""Retry utilities for transient network failures."""

import logging
from collections.abc import Callable
from typing import Any

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)


def retry_transient(is_transient: Callable[[BaseException], bool]) -> Any:
    """Return a tenacity retry decorator for transient network failures.

    Args:
        is_transient: Predicate returning ``True`` if the exception warrants a retry.

    Returns:
        A tenacity ``retry`` decorator configured with: up to 3 attempts,
        exponential backoff with jitter (initial 1 s, max 30 s), a WARNING log
        before each sleep, and reraise of the last exception after exhaustion.
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception(is_transient),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_retry.py -v
```
Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/retry.py tests/test_retry.py
git commit -m "feat: add retry_transient decorator factory"
```

---

### Task 3: Retry in MinifluxProvider

**Files:**
- Modify: `src/minizen/providers/rss/miniflux.py`
- Modify: `tests/providers/rss/test_miniflux.py`

- [ ] **Step 1: Write the failing tests**

Add the following import to the top of `tests/providers/rss/test_miniflux.py` (alongside the existing `from minizen.providers.rss.miniflux import MinifluxProvider` line):
```python
from minizen.providers.rss.miniflux import MinifluxProvider, is_transient_miniflux
```

Add these new test functions at the bottom of `tests/providers/rss/test_miniflux.py`:
```python
def test_is_transient_miniflux_returns_true_for_os_error() -> None:
    assert is_transient_miniflux(exc=OSError("timeout")) is True


def test_is_transient_miniflux_returns_true_for_5xx_client_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_response = mocker.MagicMock()
    mock_response.status_code = 503

    # act / assert
    assert is_transient_miniflux(exc=miniflux.ClientError(mock_response)) is True


def test_is_transient_miniflux_returns_false_for_4xx_client_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_response = mocker.MagicMock()
    mock_response.status_code = 403

    # act / assert
    assert is_transient_miniflux(exc=miniflux.ClientError(mock_response)) is False


def test_is_transient_miniflux_returns_false_for_other_exceptions() -> None:
    assert is_transient_miniflux(exc=ValueError("unrelated")) is False


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_retries_on_transient_error_then_succeeds(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    call_count = 0

    def flaky_get_entries(**kwargs: object) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise OSError("timeout")
        return {"total": 0, "entries": []}

    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = flaky_get_entries
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles == []
    assert call_count == 2


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_after_exhausting_retries(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = OSError("timeout")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()
    assert mock_client_cls.return_value.get_entries.call_count == 3
```

Also replace the existing `test_fetch_recent_raises_miniflux_error_on_os_error` (OSError is now transient so it retries — add sleep mock to keep it fast):
```python
@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_on_os_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = OSError("Connection refused")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()
```

- [ ] **Step 2: Run tests to verify new tests fail**

```bash
uv run pytest tests/providers/rss/test_miniflux.py::test_is_transient_miniflux_returns_true_for_os_error tests/providers/rss/test_miniflux.py::test_fetch_recent_retries_on_transient_error_then_succeeds -v
```
Expected: `ImportError` — `is_transient_miniflux` does not exist yet.

- [ ] **Step 3: Replace `src/minizen/providers/rss/miniflux.py`**

```python
"""Miniflux RSS provider for fetching articles published in the last 24 hours."""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import miniflux
from pydantic import BaseModel, Field

from minizen.exceptions import MinifluxError
from minizen.retry import retry_transient

if TYPE_CHECKING:
    from minizen.config.models import MinifluxConfig

logger = logging.getLogger(__name__)

_LOOKBACK_HOURS = 24


class Article(BaseModel):
    """A single RSS article fetched from Miniflux."""

    id: int = Field(description="Miniflux entry ID.")
    title: str = Field(description="Article title.")
    url: str = Field(description="Canonical URL of the article.")
    content: str = Field(description="Full HTML or text content of the article.")
    feed_name: str = Field(description="Name of the feed the article belongs to.")
    published_at: datetime = Field(description="Publication timestamp (UTC-aware).")
    comments_url: str | None = Field(
        default=None,
        description="URL of the article's comments section, if available.",
    )


def is_transient_miniflux(exc: BaseException) -> bool:
    """Return True if exc is a transient Miniflux error that warrants a retry.

    Args:
        exc: The exception to classify.

    Returns:
        True for ``OSError`` and ``miniflux.ClientError`` with a 5xx status code;
        False for 4xx client errors and all other exception types.
    """
    if isinstance(exc, OSError):
        return True
    if isinstance(exc, miniflux.ClientError):
        return exc.status_code >= 500
    return False


class MinifluxProvider:
    """RSS provider that reads articles via the Miniflux API."""

    def __init__(self, *, config: MinifluxConfig) -> None:
        """Initialise the Miniflux client from the given configuration.

        Args:
            config: Miniflux connection settings (URL and API key).
        """
        self._client = miniflux.Client(
            base_url=config.url,
            api_key=config.api_key,
        )

    def fetch_recent(self) -> list[Article]:
        """Return all articles from the last 24 hours, read or unread.

        Returns:
            A list of ``Article`` objects, one per entry in the lookback window.

        Raises:
            MinifluxError: If the Miniflux API call fails after all retries.
        """
        cutoff = datetime.now(tz=UTC) - timedelta(hours=_LOOKBACK_HOURS)
        after_ts = int(cutoff.timestamp())
        try:
            response = self._get_entries(after_ts=after_ts)
        except (miniflux.ClientError, OSError) as exc:
            msg = f"Miniflux API error: {exc}"
            raise MinifluxError(msg) from exc
        entries = response["entries"]
        logger.debug(
            "Fetched %d entries from the last %dh", len(entries), _LOOKBACK_HOURS
        )
        return [
            Article(
                id=entry["id"],
                title=entry["title"],
                url=entry["url"],
                content=entry["content"],
                feed_name=entry["feed"]["title"],
                published_at=datetime.fromisoformat(entry["published_at"]),
                comments_url=entry.get("comments_url") or None,
            )
            for entry in entries
        ]

    @retry_transient(is_transient_miniflux)
    def _get_entries(self, *, after_ts: int) -> dict:
        """Fetch raw entries from Miniflux, retrying on transient errors.

        Args:
            after_ts: Unix timestamp; only entries published after this are returned.

        Returns:
            Raw Miniflux API response dict.

        Raises:
            miniflux.ClientError: On API errors (retried if 5xx, re-raised if 4xx).
            OSError: On network-level failures (always retried).
        """
        return self._client.get_entries(published_after=after_ts)
```

- [ ] **Step 4: Run all Miniflux tests to verify they pass**

```bash
uv run pytest tests/providers/rss/test_miniflux.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/providers/rss/miniflux.py tests/providers/rss/test_miniflux.py
git commit -m "feat: retry transient errors in MinifluxProvider"
```

---

### Task 4: Retry in EmailProvider

**Files:**
- Modify: `src/minizen/providers/email/smtp.py`
- Modify: `tests/providers/email/test_smtp.py`

- [ ] **Step 1: Write the failing tests**

Add the following import to the top of `tests/providers/email/test_smtp.py` (alongside the existing `from minizen.providers.email.smtp import EmailProvider` line):
```python
from minizen.providers.email.smtp import EmailProvider, is_transient_smtp
```

Add these new test functions at the bottom of `tests/providers/email/test_smtp.py`:
```python
def test_is_transient_smtp_returns_true_for_os_error() -> None:
    assert is_transient_smtp(exc=OSError("network unreachable")) is True


def test_is_transient_smtp_returns_true_for_connect_error() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPConnectError(421, b"Service unavailable")) is True


def test_is_transient_smtp_returns_true_for_server_disconnected() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPServerDisconnected("disconnected")) is True


def test_is_transient_smtp_returns_false_for_auth_error() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPAuthenticationError(535, b"Bad credentials")) is False


def test_is_transient_smtp_returns_false_for_recipients_refused() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPRecipientsRefused({})) is False


def test_is_transient_smtp_returns_false_for_base_smtp_exception() -> None:
    assert is_transient_smtp(exc=smtplib.SMTPException("generic")) is False


def test_send_retries_on_transient_error_then_succeeds(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_smtp_cls = mocker.patch("minizen.providers.email.smtp.smtplib.SMTP")
    mock_smtp_cls.side_effect = [OSError("Connection refused"), mock_smtp_cls.return_value]
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
    mock_smtp.send_message.assert_called_once_with(mock_smtp.send_message.call_args[0][0])


def test_send_raises_email_error_after_exhausting_retries(mocker: MockerFixture) -> None:
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
```

Also replace the existing `test_send_raises_email_error_on_os_error` (OSError is now transient — add sleep mock):
```python
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
```

- [ ] **Step 2: Run tests to verify new tests fail**

```bash
uv run pytest tests/providers/email/test_smtp.py::test_is_transient_smtp_returns_true_for_os_error tests/providers/email/test_smtp.py::test_send_retries_on_transient_error_then_succeeds -v
```
Expected: `ImportError` — `is_transient_smtp` does not exist yet.

- [ ] **Step 3: Replace `src/minizen/providers/email/smtp.py`**

```python
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
    return isinstance(
        exc,
        (OSError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected),
    )


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
            EmailError: If the SMTP connection or send operation fails after all retries.
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
```

- [ ] **Step 4: Run all SMTP tests to verify they pass**

```bash
uv run pytest tests/providers/email/test_smtp.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest -v
```
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/providers/email/smtp.py tests/providers/email/test_smtp.py
git commit -m "feat: retry transient errors in EmailProvider"
```
