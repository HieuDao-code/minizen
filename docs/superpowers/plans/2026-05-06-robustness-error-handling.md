# Robustness — Structured Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw tracebacks with clear, actionable error messages when Miniflux, the AI model, or SMTP fails.

**Architecture:** A new `exceptions.py` module defines a `MinizenError` base class and three subclasses (`MinifluxError`, `AIError`, `EmailError`). Each provider wraps its own exceptions and re-raises as the appropriate subclass. The CLI catches `MinizenError` and prints a clean one-liner to stderr with exit code 1.

**Tech Stack:** Python stdlib (`smtplib`), `miniflux` (ClientError/ServerError), `pydantic-ai` (AgentRunError), `typer` (Exit)

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/minizen/exceptions.py` | Create | `MinizenError`, `MinifluxError`, `AIError`, `EmailError` |
| `src/minizen/providers/rss/miniflux.py` | Modify | Wrap `miniflux.ClientError`, `OSError` → `MinifluxError` |
| `src/minizen/ai/agent.py` | Modify | Wrap `AgentRunError` → `AIError` |
| `src/minizen/providers/email/smtp.py` | Modify | Wrap `SMTPException`, `OSError` → `EmailError` |
| `src/minizen/cli/commands/run.py` | Modify | Catch `MinizenError` around `run_pipeline` call |
| `src/minizen/cli/commands/digest.py` | Modify | Catch `MinizenError` in `fetch`, `preview`, `send_test` |
| `src/minizen/__init__.py` | Modify | Export exception classes in `__all__` |
| `tests/test_exceptions.py` | Create | Verify exception hierarchy |
| `tests/providers/rss/test_miniflux.py` | Modify | Add `MinifluxError` wrapping tests |
| `tests/ai/test_agent.py` | Modify | Add `AIError` wrapping test |
| `tests/providers/email/test_smtp.py` | Modify | Add `EmailError` wrapping tests |
| `tests/cli/commands/test_run.py` | Modify | Add `MinizenError` CLI handling test |
| `tests/cli/commands/test_digest.py` | Modify | Add `MinizenError` CLI handling tests |
| `tests/test_public_api.py` | Modify | Verify exception exports |

---

## Task 1: Create the exceptions module

**Files:**
- Create: `src/minizen/exceptions.py`
- Create: `tests/test_exceptions.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_exceptions.py`:

```python
from minizen.exceptions import AIError, EmailError, MinifluxError, MinizenError


def test_minizen_error_is_exception() -> None:
    # act / assert
    assert issubclass(MinizenError, Exception)


def test_miniflux_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(MinifluxError, MinizenError)


def test_ai_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(AIError, MinizenError)


def test_email_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(EmailError, MinizenError)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_exceptions.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.exceptions'`

- [ ] **Step 3: Create `src/minizen/exceptions.py`**

```python
"""Custom exceptions for minizen error handling."""


class MinizenError(Exception):
    """Base exception for all minizen errors."""


class MinifluxError(MinizenError):
    """Raised when the Miniflux API or network request fails."""


class AIError(MinizenError):
    """Raised when the AI model call fails."""


class EmailError(MinizenError):
    """Raised when the email delivery fails."""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_exceptions.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/exceptions.py tests/test_exceptions.py
git commit -m "feat: add MinizenError exception hierarchy"
```

---

## Task 2: Add error handling to MinifluxProvider

**Files:**
- Modify: `src/minizen/providers/rss/miniflux.py`
- Modify: `tests/providers/rss/test_miniflux.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/providers/rss/test_miniflux.py`:

```python
import pytest

import miniflux

from minizen.exceptions import MinifluxError


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_on_client_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_response = mocker.MagicMock()
    mock_response.status_code = 403
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error_message": "Forbidden"}
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = miniflux.ClientError(
        mock_response
    )
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_on_os_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = OSError("Connection refused")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/providers/rss/test_miniflux.py::test_fetch_recent_raises_miniflux_error_on_client_error tests/providers/rss/test_miniflux.py::test_fetch_recent_raises_miniflux_error_on_os_error -v
```

Expected: 2 tests FAIL — `miniflux.ClientError` and `OSError` propagate unwrapped.

- [ ] **Step 3: Update `src/minizen/providers/rss/miniflux.py`**

Add the import at the top of the file (after existing imports):

```python
from minizen.exceptions import MinifluxError
```

Replace the `fetch_recent` method body:

```python
def fetch_recent(self) -> list[Article]:
    """Return all articles from the last 24 hours, read or unread.

    Returns:
        A list of ``Article`` objects, one per entry in the lookback window.

    Raises:
        MinifluxError: If the Miniflux API call fails due to a client error or
            network issue.
    """
    cutoff = datetime.now(tz=UTC) - timedelta(hours=_LOOKBACK_HOURS)
    after_ts = int(cutoff.timestamp())
    try:
        response = self._client.get_entries(published_after=after_ts)
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
```

Note: `miniflux.ServerError` inherits from `miniflux.ClientError`, so catching `miniflux.ClientError` already covers server errors.

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/providers/rss/test_miniflux.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/providers/rss/miniflux.py tests/providers/rss/test_miniflux.py
git commit -m "feat: wrap Miniflux API errors as MinifluxError"
```

---

## Task 3: Add error handling to DigestAgent

**Files:**
- Modify: `src/minizen/ai/agent.py`
- Modify: `tests/ai/test_agent.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/ai/test_agent.py`:

```python
import pytest
from pydantic_ai.exceptions import UnexpectedModelBehavior

from minizen.exceptions import AIError


def test_run_raises_ai_error_on_model_failure(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_agent_cls.return_value.run_sync.side_effect = UnexpectedModelBehavior(
        "Model returned empty response"
    )
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=5)
    articles = [_make_article(article_id=1)]

    # act / assert
    with pytest.raises(AIError, match="AI model error"):
        agent.run(articles=articles)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/ai/test_agent.py::test_run_raises_ai_error_on_model_failure -v
```

Expected: FAIL — `UnexpectedModelBehavior` propagates unwrapped.

- [ ] **Step 3: Update `src/minizen/ai/agent.py`**

Add imports after existing imports:

```python
from pydantic_ai.exceptions import AgentRunError

from minizen.exceptions import AIError
```

Replace the final two lines of the `run` method (the `result = ...` and `return cast(...)` lines):

```python
        try:
            result = self._agent.run_sync(user_prompt)
        except AgentRunError as exc:
            msg = f"AI model error: {exc}"
            raise AIError(msg) from exc
        return cast("AgentRunResult[DigestResult]", result).output
```

The full updated `run` method should end as:

```python
    def run(self, *, articles: list[Article]) -> DigestResult:
        """Select the top N articles and return a structured Markdown digest.

        Args:
            articles: Full list of articles to choose from.

        Returns:
            A ``DigestResult`` containing the Markdown text and the IDs of
            articles that were included.

        Raises:
            AIError: If the AI model call fails.
        """
        logger.info("Running AI agent on %d article(s)", len(articles))
        articles_text = "\n\n---\n\n".join(
            f"ID: {a.id}\n"
            f"Feed: {a.feed_name}\n"
            f"Title: {a.title}\n"
            f"URL: {a.url}\n"
            f"Published: {a.published_at.isoformat()}\n"
            + (f"Comments URL: {a.comments_url}\n" if a.comments_url else "")
            + f"\n{_truncate_words(a.content, self._max_words_per_article)}"
            for a in articles
        )
        user_prompt = (
            f"Please select the top {self._top_n} most important articles "  # noqa: S608
            f"from the following and write a digest:\n\n{articles_text}"
        )
        try:
            result = self._agent.run_sync(user_prompt)
        except AgentRunError as exc:
            msg = f"AI model error: {exc}"
            raise AIError(msg) from exc
        return cast("AgentRunResult[DigestResult]", result).output
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat: wrap pydantic-ai errors as AIError"
```

---

## Task 4: Add error handling to EmailProvider

**Files:**
- Modify: `src/minizen/providers/email/smtp.py`
- Modify: `tests/providers/email/test_smtp.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/providers/email/test_smtp.py`:

```python
import smtplib

import pytest

from minizen.exceptions import EmailError


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

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/providers/email/test_smtp.py::test_send_raises_email_error_on_smtp_exception tests/providers/email/test_smtp.py::test_send_raises_email_error_on_os_error -v
```

Expected: 2 tests FAIL — exceptions propagate unwrapped.

- [ ] **Step 3: Update `src/minizen/providers/email/smtp.py`**

Add import after existing imports:

```python
from minizen.exceptions import EmailError
```

Replace the `send` method's `with smtplib.SMTP(...)` block:

```python
    def send(self, *, subject: str, html: str, plain_text: str = "") -> None:
        """Send an email with an HTML body and an optional plain-text fallback.

        Args:
            subject: Email subject line.
            html: HTML body of the message.
            plain_text: Optional plain-text alternative; omitted if empty.

        Raises:
            EmailError: If the SMTP connection or send operation fails.
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
        except (smtplib.SMTPException, OSError) as exc:
            err_msg = f"Email delivery failed: {exc}"
            raise EmailError(err_msg) from exc
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/providers/email/test_smtp.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/providers/email/smtp.py tests/providers/email/test_smtp.py
git commit -m "feat: wrap SMTP errors as EmailError"
```

---

## Task 5: Add MinizenError handling to CLI commands

**Files:**
- Modify: `src/minizen/cli/commands/run.py`
- Modify: `src/minizen/cli/commands/digest.py`
- Modify: `tests/cli/commands/test_run.py`
- Modify: `tests/cli/commands/test_digest.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/commands/test_run.py`:

```python
from minizen.exceptions import MinifluxError


def test_run_prints_error_and_exits_on_minizen_error(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_settings = MagicMock()
    mock_settings.miniflux.model_copy.return_value = mock_settings.miniflux
    mock_settings.email.model_copy.return_value = mock_settings.email
    mock_settings.ai.model_copy.return_value = mock_settings.ai
    mock_settings.model_copy.return_value = mock_settings
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=mock_settings)
    mocker.patch(
        "minizen.cli.commands.run.run_pipeline",
        side_effect=MinifluxError("Miniflux API error: 403 Forbidden"),
    )
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run", "--config", str(config_path)])

    # assert
    assert result.exit_code == 1
    assert "Error: Miniflux API error: 403 Forbidden" in result.output
```

Append to `tests/cli/commands/test_digest.py`:

```python
from minizen.exceptions import AIError, EmailError, MinifluxError


def test_digest_fetch_prints_error_and_exits_on_miniflux_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = mocker.MagicMock()
    mock_rss.fetch_recent.side_effect = MinifluxError("Miniflux API error: timeout")
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "fetch"])

    # assert
    assert result.exit_code == 1
    assert "Error: Miniflux API error: timeout" in result.output


def test_digest_preview_prints_error_and_exits_on_minizen_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = mocker.MagicMock()
    mock_rss.fetch_recent.side_effect = AIError("AI model error: quota exceeded")
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "preview"])

    # assert
    assert result.exit_code == 1
    assert "Error: AI model error: quota exceeded" in result.output


def test_digest_send_test_prints_error_and_exits_on_minizen_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = mocker.MagicMock()
    mock_rss.fetch_recent.side_effect = EmailError("Email delivery failed: SMTP auth")
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "send-test"])

    # assert
    assert result.exit_code == 1
    assert "Error: Email delivery failed: SMTP auth" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/cli/commands/test_run.py::test_run_prints_error_and_exits_on_minizen_error tests/cli/commands/test_digest.py::test_digest_fetch_prints_error_and_exits_on_miniflux_error tests/cli/commands/test_digest.py::test_digest_preview_prints_error_and_exits_on_minizen_error tests/cli/commands/test_digest.py::test_digest_send_test_prints_error_and_exits_on_minizen_error -v
```

Expected: 4 tests FAIL — exceptions propagate uncaught, `exit_code` is not 1.

- [ ] **Step 3: Update `src/minizen/cli/commands/run.py`**

Add import after the existing imports:

```python
from minizen.exceptions import MinizenError
```

Replace the last line of the `run` function (`run_pipeline(settings=settings, dry_run=dry_run)`) with:

```python
    try:
        run_pipeline(settings=settings, dry_run=dry_run)
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 4: Update `src/minizen/cli/commands/digest.py`**

Add import after the existing imports:

```python
from minizen.exceptions import MinizenError
```

In the `fetch` command, wrap the provider call. Replace:

```python
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_recent()
    if not articles:
        typer.echo("No recent articles.")
        return
    typer.echo(f"{len(articles)} recent article(s) in the last 24h:\n")
    for article in articles:
        typer.echo(f"[{article.feed_name}] {article.title}")
        typer.echo(f"  {article.url}")
```

With:

```python
    rss = MinifluxProvider(config=settings.miniflux)
    try:
        articles = rss.fetch_recent()
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    if not articles:
        typer.echo("No recent articles.")
        return
    typer.echo(f"{len(articles)} recent article(s) in the last 24h:\n")
    for article in articles:
        typer.echo(f"[{article.feed_name}] {article.title}")
        typer.echo(f"  {article.url}")
```

In the `preview` command, wrap the provider and agent calls. Replace:

```python
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_recent()
    if not articles:
        typer.echo("No recent articles.")
        return
    if dry_run:
        typer.echo(f"{len(articles)} recent article(s) in the last 24h:\n")
        for article in articles:
            typer.echo(f"[{article.feed_name}] {article.title}")
            typer.echo(f"  {article.url}")
        return
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        max_words_per_article=settings.ai.max_words_per_article,
    )
    result = agent.run(articles=articles)
    typer.echo(result.markdown)
```

With:

```python
    rss = MinifluxProvider(config=settings.miniflux)
    try:
        articles = rss.fetch_recent()
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    if not articles:
        typer.echo("No recent articles.")
        return
    if dry_run:
        typer.echo(f"{len(articles)} recent article(s) in the last 24h:\n")
        for article in articles:
            typer.echo(f"[{article.feed_name}] {article.title}")
            typer.echo(f"  {article.url}")
        return
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        max_words_per_article=settings.ai.max_words_per_article,
    )
    try:
        result = agent.run(articles=articles)
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(result.markdown)
```

In the `send_test` command, wrap the provider, agent, and email calls. Replace:

```python
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_recent()
    if not articles:
        typer.echo("No recent articles.")
        return
    if dry_run:
        typer.confirm(
            "This will make a real LLM API call but will not send an email. Continue?",
            abort=True,
        )
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        max_words_per_article=settings.ai.max_words_per_article,
    )
    result = agent.run(articles=articles)
    selected_ids = set(result.articles_used)
    extra_articles = [a for a in articles if a.id not in selected_ids]
    html, plain_text = render_email(result.markdown, extra_articles=extra_articles)
    if dry_run:
        typer.echo("Dry run — email not sent:\n")
        typer.echo(plain_text)
        return
    today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
    email = EmailProvider(config=settings.email)
    email.send(
        subject=f"[TEST] Your Daily Zen — {today}",
        html=html,
        plain_text=plain_text,
    )
    typer.echo("Test digest sent.")
```

With:

```python
    rss = MinifluxProvider(config=settings.miniflux)
    try:
        articles = rss.fetch_recent()
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    if not articles:
        typer.echo("No recent articles.")
        return
    if dry_run:
        typer.confirm(
            "This will make a real LLM API call but will not send an email. Continue?",
            abort=True,
        )
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        max_words_per_article=settings.ai.max_words_per_article,
    )
    try:
        result = agent.run(articles=articles)
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    selected_ids = set(result.articles_used)
    extra_articles = [a for a in articles if a.id not in selected_ids]
    html, plain_text = render_email(result.markdown, extra_articles=extra_articles)
    if dry_run:
        typer.echo("Dry run — email not sent:\n")
        typer.echo(plain_text)
        return
    today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
    email = EmailProvider(config=settings.email)
    try:
        email.send(
            subject=f"[TEST] Your Daily Zen — {today}",
            html=html,
            plain_text=plain_text,
        )
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo("Test digest sent.")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/cli/commands/test_run.py tests/cli/commands/test_digest.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/run.py src/minizen/cli/commands/digest.py tests/cli/commands/test_run.py tests/cli/commands/test_digest.py
git commit -m "feat: catch MinizenError in CLI commands and exit cleanly"
```

---

## Task 6: Export exceptions from public API

**Files:**
- Modify: `src/minizen/__init__.py`
- Modify: `tests/test_public_api.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_public_api.py`, add to the imports at the top:

```python
from minizen import (
    AIError,
    EmailError,
    MinifluxError,
    MinizenError,
    # ... existing imports ...
)
from minizen.exceptions import (
    AIError as _AIError,
    EmailError as _EmailError,
    MinifluxError as _MinifluxError,
    MinizenError as _MinizenError,
)
```

Add to `test_top_level_all`:

```python
    expected = {
        "AIConfig",
        "AIError",
        "Article",
        "DigestAgent",
        "DigestResult",
        "EmailConfig",
        "EmailError",
        "EmailProvider",
        "MinifluxConfig",
        "MinifluxError",
        "MinifluxProvider",
        "MinizenError",
        "Settings",
        "load_settings",
        "run_pipeline",
    }
```

Add a new test:

```python
def test_exception_imports_are_same_objects() -> None:
    # assert
    assert MinizenError is _MinizenError
    assert MinifluxError is _MinifluxError
    assert AIError is _AIError
    assert EmailError is _EmailError
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_public_api.py -v
```

Expected: FAIL — `ImportError: cannot import name 'MinizenError' from 'minizen'`

- [ ] **Step 3: Update `src/minizen/__init__.py`**

Add import and update `__all__`:

```python
"""minizen — A quieter way to stay informed."""

from minizen.ai import DigestAgent, DigestResult
from minizen.config import (
    AIConfig,
    EmailConfig,
    MinifluxConfig,
    Settings,
    load_settings,
)
from minizen.core import run_pipeline
from minizen.exceptions import AIError, EmailError, MinifluxError, MinizenError
from minizen.providers.email import EmailProvider
from minizen.providers.rss import Article, MinifluxProvider

__version__ = "0.3.0"

__all__ = [
    "AIConfig",
    "AIError",
    "Article",
    "DigestAgent",
    "DigestResult",
    "EmailConfig",
    "EmailError",
    "EmailProvider",
    "MinifluxConfig",
    "MinifluxError",
    "MinifluxProvider",
    "MinizenError",
    "Settings",
    "load_settings",
    "run_pipeline",
]
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest -v
```

Expected: all tests PASS with 100% coverage.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/__init__.py tests/test_public_api.py
git commit -m "feat: export exception classes from public API"
```
