# minizen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Typer CLI that fetches unread RSS articles from Miniflux, uses a pydantic-ai agent to curate and summarise the top N most interesting into a Markdown digest, converts it to HTML, and emails it — scheduled daily via GitHub Actions.

**Architecture:** Layered modules with clean interfaces: `config/` (TOML + env), `providers/rss/` (Miniflux), `providers/email/` (SMTP), `ai/` (pydantic-ai agent), `core/pipeline.py` (orchestration), `cli/` (Typer app). Each layer communicates through typed Pydantic models. The CLI is a thin wrapper over the core pipeline.

**Tech Stack:** Python 3.14, Typer, pydantic-ai-slim[anthropic,openai], miniflux, mistune, smtplib (stdlib), tomllib (stdlib), python-dotenv, tomli-w, pytest, ruff, ty.

---

## File Map

```
src/minizen/
  __init__.py               (existing, keep)
  main.py                   (modify — CLI entrypoint)
  core/
    __init__.py             (create — version string for commitizen)
    pipeline.py             (create — fetch → summarise → send orchestration)
  config/
    __init__.py             (create — empty)
    models.py               (create — Pydantic Settings models)
    loader.py               (create — load TOML + env vars into Settings)
  providers/
    __init__.py             (create — empty)
    rss/
      __init__.py           (create — empty)
      miniflux.py           (create — Miniflux client wrapper, Article model)
    email/
      __init__.py           (create — empty)
      smtp.py               (create — SMTP sender)
  ai/
    __init__.py             (create — empty)
    agent.py                (create — pydantic-ai curation agent, DigestResult model)
  cli/
    __init__.py             (create — Typer app, register subcommands)
    commands/
      __init__.py           (create — empty)
      run.py                (create — minizen run)
      config.py             (create — minizen config show/validate/set)
      digest.py             (create — minizen digest preview/send-test)
      setup.py              (create — minizen setup wizard)

tests/
  __init__.py               (existing, keep)
  test_hello.py             (delete — replaced by module-level tests)
  config/
    __init__.py             (create — empty)
    test_models.py          (create)
    test_loader.py          (create)
  providers/
    __init__.py             (create — empty)
    rss/
      __init__.py           (create — empty)
      test_miniflux.py      (create)
    email/
      __init__.py           (create — empty)
      test_smtp.py          (create)
  ai/
    __init__.py             (create — empty)
    test_agent.py           (create)
  core/
    __init__.py             (create — empty)
    test_pipeline.py        (create)
  cli/
    __init__.py             (create — empty)
    test_run.py             (create)
    test_config.py          (create)
    test_digest.py          (create)
    test_setup.py           (create)

.github/
  workflows/
    daily-digest.yml        (create)
```

---

## Task 1: Project scaffolding

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/minizen/main.py`
- Create: `src/minizen/core/__init__.py`
- Delete: `tests/test_hello.py`

- [ ] **Step 1: Add missing runtime dependencies and entry point to pyproject.toml**

In `pyproject.toml`, update the `dependencies` list and add a `[project.scripts]` section:

```toml
[project]
name = "minizen"
version = "0.1.0"
description = "A quieter way to stay informed"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
  "miniflux>=1.1.6,<2.0.0",
  "mistune>=3.1.3,<4.0.0",
  "pydantic>=2.13.1,<3.0.0",
  "pydantic-ai-slim[anthropic,openai]>=1.84.0,<2.0.0",
  "python-dotenv>=1.1.0,<2.0.0",
  "tomli-w>=1.0.0,<2.0.0",
  "typer>=0.24.1,<0.25.0",
]

[project.scripts]
minizen = "minizen.main:app"
```

- [ ] **Step 2: Lock updated dependencies**

```bash
uv lock
```

Expected: lock file regenerated with no errors.

- [ ] **Step 3: Create the version file that commitizen tracks**

Create `src/minizen/core/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Replace main.py with the CLI entrypoint**

Replace `src/minizen/main.py` with:

```python
from minizen.cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 5: Delete the stub test**

```bash
rm tests/test_hello.py
```

- [ ] **Step 6: Verify the package installs and --help works**

```bash
uv run minizen --help
```

Expected: Typer prints help text (even though no commands are wired yet, the import must succeed).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock src/minizen/main.py src/minizen/core/__init__.py
git rm tests/test_hello.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

## Task 2: Config models

**Files:**
- Create: `src/minizen/config/__init__.py`
- Create: `src/minizen/config/models.py`
- Create: `tests/config/__init__.py`
- Create: `tests/config/test_models.py`

- [ ] **Step 1: Create empty init files**

```bash
mkdir -p src/minizen/config tests/config
touch src/minizen/config/__init__.py tests/config/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/config/test_models.py`:

```python
import pytest
from pydantic import ValidationError

from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def test_miniflux_config_accepts_valid_values() -> None:
    # act
    config = MinifluxConfig(url="https://rss.example.com", api_key="key123")

    # assert
    assert config.url == "https://rss.example.com"
    assert config.api_key == "key123"


def test_email_config_accepts_valid_values() -> None:
    # act
    config = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )

    # assert
    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.from_addr == "from@example.com"
    assert config.to_addr == "to@example.com"
    assert config.username == "user"
    assert config.password == "pass"


def test_ai_config_defaults() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.model == "anthropic:claude-sonnet-4-6"
    assert config.top_n == 5


def test_ai_config_accepts_custom_values() -> None:
    # act
    config = AIConfig(model="openai:gpt-4o", top_n=3)

    # assert
    assert config.model == "openai:gpt-4o"
    assert config.top_n == 3


def test_settings_composes_sub_configs() -> None:
    # arrange
    miniflux = MinifluxConfig(url="https://rss.example.com", api_key="key")
    email = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="a@example.com",
        to_addr="b@example.com",
        username="user",
        password="pass",
    )
    ai = AIConfig()

    # act
    settings = Settings(miniflux=miniflux, email=email, ai=ai)

    # assert
    assert settings.miniflux.url == "https://rss.example.com"
    assert settings.email.smtp_host == "smtp.example.com"
    assert settings.ai.top_n == 5


def test_settings_requires_miniflux() -> None:
    # act / assert
    with pytest.raises(ValidationError):
        Settings(
            email=EmailConfig(
                smtp_host="smtp.example.com",
                smtp_port=587,
                from_addr="a@example.com",
                to_addr="b@example.com",
                username="user",
                password="pass",
            ),
            ai=AIConfig(),
        )
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/config/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.config.models'`

- [ ] **Step 4: Create the models**

Create `src/minizen/config/models.py`:

```python
from pydantic import BaseModel


class MinifluxConfig(BaseModel):
    url: str
    api_key: str


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    from_addr: str
    to_addr: str
    username: str
    password: str


class AIConfig(BaseModel):
    model: str = "anthropic:claude-sonnet-4-6"
    top_n: int = 5


class Settings(BaseModel):
    miniflux: MinifluxConfig
    email: EmailConfig
    ai: AIConfig
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/config/test_models.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/config/ tests/config/test_models.py tests/config/__init__.py
git commit -m "feat: add config pydantic models"
```

---

## Task 3: Config loader

**Files:**
- Create: `src/minizen/config/loader.py`
- Create: `tests/config/test_loader.py`

- [ ] **Step 1: Write failing tests**

Create `tests/config/test_loader.py`:

```python
import tomllib
from pathlib import Path

import pytest
import tomli_w

from minizen.config.loader import load_settings


def _write_config(path: Path, data: dict) -> None:
    path.write_bytes(tomli_w.dumps(data).encode())


def test_load_settings_reads_toml_and_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
            "ai": {"model": "anthropic:claude-sonnet-4-6", "top_n": 5},
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("EMAIL_PASSWORD", "email-pass")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")

    # act
    settings = load_settings(config_path=config_file)

    # assert
    assert settings.miniflux.url == "https://rss.example.com"
    assert settings.miniflux.api_key == "mf-key"
    assert settings.email.smtp_host == "smtp.example.com"
    assert settings.email.smtp_port == 587
    assert settings.email.username == "email-user"
    assert settings.email.password == "email-pass"
    assert settings.ai.model == "anthropic:claude-sonnet-4-6"
    assert settings.ai.top_n == 5


def test_load_settings_uses_ai_defaults_when_section_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("EMAIL_PASSWORD", "email-pass")

    # act
    settings = load_settings(config_path=config_file)

    # assert
    assert settings.ai.model == "anthropic:claude-sonnet-4-6"
    assert settings.ai.top_n == 5


def test_load_settings_raises_when_env_var_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        },
    )
    monkeypatch.delenv("MINIFLUX_API_KEY", raising=False)

    # act / assert
    with pytest.raises(KeyError, match="MINIFLUX_API_KEY"):
        load_settings(config_path=config_file)


def test_load_settings_raises_when_config_file_missing(tmp_path: Path) -> None:
    # act / assert
    with pytest.raises(FileNotFoundError):
        load_settings(config_path=tmp_path / "missing.toml")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/config/test_loader.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.config.loader'`

- [ ] **Step 3: Create the loader**

Create `src/minizen/config/loader.py`:

```python
import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def load_settings(*, config_path: Path) -> Settings:
    load_dotenv()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    ai_raw = raw.get("ai", {})

    return Settings(
        miniflux=MinifluxConfig(
            url=raw["miniflux"]["url"],
            api_key=os.environ["MINIFLUX_API_KEY"],
        ),
        email=EmailConfig(
            smtp_host=raw["email"]["smtp_host"],
            smtp_port=raw["email"]["smtp_port"],
            from_addr=raw["email"]["from_addr"],
            to_addr=raw["email"]["to_addr"],
            username=os.environ["EMAIL_USERNAME"],
            password=os.environ["EMAIL_PASSWORD"],
        ),
        ai=AIConfig(
            model=ai_raw.get("model", "anthropic:claude-sonnet-4-6"),
            top_n=ai_raw.get("top_n", 5),
        ),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/config/test_loader.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/loader.py tests/config/test_loader.py
git commit -m "feat: add config loader"
```

---

## Task 4: RSS provider

**Files:**
- Create: `src/minizen/providers/__init__.py`
- Create: `src/minizen/providers/rss/__init__.py`
- Create: `src/minizen/providers/rss/miniflux.py`
- Create: `tests/providers/__init__.py`
- Create: `tests/providers/rss/__init__.py`
- Create: `tests/providers/rss/test_miniflux.py`

- [ ] **Step 1: Create empty init files**

```bash
mkdir -p src/minizen/providers/rss tests/providers/rss
touch src/minizen/providers/__init__.py
touch src/minizen/providers/rss/__init__.py
touch tests/providers/__init__.py
touch tests/providers/rss/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/providers/rss/test_miniflux.py`:

```python
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from minizen.config.models import MinifluxConfig
from minizen.providers.rss.miniflux import Article, MinifluxProvider


def test_fetch_unread_returns_articles(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 42,
                "title": "Test Article",
                "url": "https://example.com/article",
                "content": "<p>Body</p>",
                "feed": {"title": "Example Feed"},
                "published_at": "2026-04-24T08:00:00Z",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert len(articles) == 1
    assert articles[0].id == 42
    assert articles[0].title == "Test Article"
    assert articles[0].url == "https://example.com/article"
    assert articles[0].content == "<p>Body</p>"
    assert articles[0].feed_name == "Example Feed"
    assert articles[0].published_at == datetime(2026, 4, 24, 8, 0, 0, tzinfo=timezone.utc)
    mock_client_cls.return_value.get_entries.assert_called_once_with(status=["unread"])


def test_fetch_unread_returns_empty_list_when_no_entries(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {"total": 0, "entries": []}
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert articles == []


def test_mark_as_read_calls_client_with_ids(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    provider.mark_as_read(article_ids=[1, 2, 3])

    # assert
    mock_client_cls.return_value.update_entries.assert_called_once_with(
        entry_ids=[1, 2, 3], status="read"
    )


def test_miniflux_client_initialized_with_config(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    config = MinifluxConfig(url="https://rss.example.com", api_key="secret-key")

    # act
    MinifluxProvider(config=config)

    # assert
    mock_client_cls.assert_called_once_with(
        base_url="https://rss.example.com", api_key="secret-key"
    )
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/providers/rss/test_miniflux.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.providers.rss.miniflux'`

- [ ] **Step 4: Create the RSS provider**

Create `src/minizen/providers/rss/miniflux.py`:

```python
from datetime import datetime, timezone

import miniflux
from pydantic import BaseModel

from minizen.config.models import MinifluxConfig


class Article(BaseModel):
    id: int
    title: str
    url: str
    content: str
    feed_name: str
    published_at: datetime


class MinifluxProvider:
    def __init__(self, *, config: MinifluxConfig) -> None:
        self._client = miniflux.Client(
            base_url=config.url,
            api_key=config.api_key,
        )

    def fetch_unread(self) -> list[Article]:
        response = self._client.get_entries(status=["unread"])
        return [
            Article(
                id=entry["id"],
                title=entry["title"],
                url=entry["url"],
                content=entry["content"],
                feed_name=entry["feed"]["title"],
                published_at=datetime.fromisoformat(
                    entry["published_at"].replace("Z", "+00:00")
                ),
            )
            for entry in response["entries"]
        ]

    def mark_as_read(self, *, article_ids: list[int]) -> None:
        self._client.update_entries(entry_ids=article_ids, status="read")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/providers/rss/test_miniflux.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/providers/ tests/providers/
git commit -m "feat: add miniflux RSS provider"
```

---

## Task 5: Email provider

**Files:**
- Create: `src/minizen/providers/email/__init__.py`
- Create: `src/minizen/providers/email/smtp.py`
- Create: `tests/providers/email/__init__.py`
- Create: `tests/providers/email/test_smtp.py`

- [ ] **Step 1: Create empty init files**

```bash
mkdir -p src/minizen/providers/email tests/providers/email
touch src/minizen/providers/email/__init__.py tests/providers/email/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/providers/email/test_smtp.py`:

```python
import smtplib
from email.mime.multipart import MIMEMultipart

from pytest_mock import MockerFixture

from minizen.config.models import EmailConfig
from minizen.providers.email.smtp import EmailProvider


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
    mock_smtp.send_message.assert_called_once()


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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/providers/email/test_smtp.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.providers.email.smtp'`

- [ ] **Step 4: Create the email provider**

Create `src/minizen/providers/email/smtp.py`:

```python
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

        with smtplib.SMTP(host=self._config.smtp_host, port=self._config.smtp_port) as server:
            server.starttls()
            server.login(user=self._config.username, password=self._config.password)
            server.send_message(msg)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/providers/email/test_smtp.py -v
```

Expected: all 2 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/providers/email/ tests/providers/email/
git commit -m "feat: add SMTP email provider"
```

---

## Task 6: AI agent

**Files:**
- Create: `src/minizen/ai/__init__.py`
- Create: `src/minizen/ai/agent.py`
- Create: `tests/ai/__init__.py`
- Create: `tests/ai/test_agent.py`

- [ ] **Step 1: Create empty init files**

```bash
mkdir -p src/minizen/ai tests/ai
touch src/minizen/ai/__init__.py tests/ai/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/ai/test_agent.py`:

```python
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from minizen.ai.agent import DigestAgent, DigestResult
from minizen.providers.rss.miniflux import Article


def _make_article(*, article_id: int = 1) -> Article:
    return Article(
        id=article_id,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=timezone.utc),
    )


def test_run_returns_digest_result(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.data = DigestResult(
        markdown="# Digest\n\nSome news.",
        articles_used=[1],
    )
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=5)
    articles = [_make_article(article_id=1)]

    # act
    result = agent.run(articles=articles)

    # assert
    assert result.markdown == "# Digest\n\nSome news."
    assert result.articles_used == [1]
    mock_agent_cls.return_value.run_sync.assert_called_once()


def test_run_passes_article_data_to_agent(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.data = DigestResult(markdown="# Digest", articles_used=[42])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=42)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Test Article" in user_prompt
    assert "Test Feed" in user_prompt
    assert "42" in user_prompt


def test_agent_initialized_with_correct_model(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(model="openai:gpt-4o", top_n=3)

    # assert
    mock_agent_cls.assert_called_once()
    call_kwargs = mock_agent_cls.call_args[1]
    assert call_kwargs["model"] == "openai:gpt-4o"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.ai.agent'`

- [ ] **Step 4: Create the AI agent**

Create `src/minizen/ai/agent.py`:

```python
from pydantic import BaseModel
from pydantic_ai import Agent

from minizen.providers.rss.miniflux import Article

_SYSTEM_PROMPT = """\
You are a personal news curator. You receive a list of unread articles and must:
1. Select the top N most important and interesting articles.
2. Write a cohesive, well-structured Markdown digest covering those articles.
3. Return the digest and the IDs of the articles you selected.

Be concise. Prioritise articles with broad significance over niche topics.
"""


class DigestResult(BaseModel):
    markdown: str
    articles_used: list[int]


class DigestAgent:
    def __init__(self, *, model: str, top_n: int) -> None:
        self._top_n = top_n
        self._agent: Agent[None, DigestResult] = Agent(
            model=model,
            result_type=DigestResult,
            system_prompt=_SYSTEM_PROMPT,
        )

    def run(self, *, articles: list[Article]) -> DigestResult:
        articles_text = "\n\n---\n\n".join(
            f"ID: {a.id}\n"
            f"Feed: {a.feed_name}\n"
            f"Title: {a.title}\n"
            f"URL: {a.url}\n"
            f"Published: {a.published_at.isoformat()}\n\n"
            f"{a.content}"
            for a in articles
        )
        user_prompt = (
            f"Please select the top {self._top_n} most important articles "
            f"from the following and write a digest:\n\n{articles_text}"
        )
        result = self._agent.run_sync(user_prompt)
        return result.data
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/ai/ tests/ai/
git commit -m "feat: add pydantic-ai digest agent"
```

---

## Task 7: Core pipeline

**Files:**
- Create: `src/minizen/core/pipeline.py`
- Create: `tests/core/__init__.py`
- Create: `tests/core/test_pipeline.py`

- [ ] **Step 1: Create empty init files**

```bash
mkdir -p tests/core
touch tests/core/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/core/test_pipeline.py`:

```python
import logging
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from minizen.ai.agent import DigestResult
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings
from minizen.core.pipeline import run_pipeline
from minizen.providers.rss.miniflux import Article


def _make_settings() -> Settings:
    return Settings(
        miniflux=MinifluxConfig(url="https://rss.example.com", api_key="key"),
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="from@example.com",
            to_addr="to@example.com",
            username="user",
            password="pass",
        ),
        ai=AIConfig(model="anthropic:claude-sonnet-4-6", top_n=5),
    )


def _make_article(*, article_id: int = 1) -> Article:
    return Article(
        id=article_id,
        title="Test",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=timezone.utc),
    )


def test_pipeline_runs_full_flow(mocker: MockerFixture) -> None:
    # arrange
    mock_rss_cls = mocker.patch("minizen.core.pipeline.MinifluxProvider")
    mock_email_cls = mocker.patch("minizen.core.pipeline.EmailProvider")
    mock_agent_cls = mocker.patch("minizen.core.pipeline.DigestAgent")
    mock_html = mocker.patch("minizen.core.pipeline.mistune.html", return_value="<h1>Digest</h1>")

    articles = [_make_article(article_id=1)]
    mock_rss_cls.return_value.fetch_unread.return_value = articles
    mock_agent_cls.return_value.run.return_value = DigestResult(
        markdown="# Digest", articles_used=[1]
    )

    # act
    run_pipeline(settings=_make_settings())

    # assert
    mock_rss_cls.return_value.fetch_unread.assert_called_once_with()
    mock_agent_cls.return_value.run.assert_called_once_with(articles=articles)
    mock_html.assert_called_once_with("# Digest")
    mock_email_cls.return_value.send.assert_called_once_with(
        subject="Your daily digest", html="<h1>Digest</h1>"
    )
    mock_rss_cls.return_value.mark_as_read.assert_called_once_with(article_ids=[1])


def test_pipeline_exits_early_when_no_articles(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    # arrange
    mock_rss_cls = mocker.patch("minizen.core.pipeline.MinifluxProvider")
    mock_email_cls = mocker.patch("minizen.core.pipeline.EmailProvider")
    mock_agent_cls = mocker.patch("minizen.core.pipeline.DigestAgent")
    mock_rss_cls.return_value.fetch_unread.return_value = []

    # act
    with caplog.at_level(logging.INFO):
        run_pipeline(settings=_make_settings())

    # assert
    assert "No unread articles" in caplog.text
    mock_agent_cls.return_value.run.assert_not_called()
    mock_email_cls.return_value.send.assert_not_called()
    mock_rss_cls.return_value.mark_as_read.assert_not_called()


def test_pipeline_does_not_mark_read_when_email_fails(mocker: MockerFixture) -> None:
    # arrange
    mock_rss_cls = mocker.patch("minizen.core.pipeline.MinifluxProvider")
    mock_email_cls = mocker.patch("minizen.core.pipeline.EmailProvider")
    mock_agent_cls = mocker.patch("minizen.core.pipeline.DigestAgent")
    mocker.patch("minizen.core.pipeline.mistune.html", return_value="<h1>Digest</h1>")

    mock_rss_cls.return_value.fetch_unread.return_value = [_make_article()]
    mock_agent_cls.return_value.run.return_value = DigestResult(
        markdown="# Digest", articles_used=[1]
    )
    mock_email_cls.return_value.send.side_effect = OSError("SMTP connection refused")

    # act / assert
    with pytest.raises(OSError):
        run_pipeline(settings=_make_settings())

    mock_rss_cls.return_value.mark_as_read.assert_not_called()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/core/test_pipeline.py -v
```

Expected: `ModuleNotFoundError: No module named 'minizen.core.pipeline'`

- [ ] **Step 4: Create the pipeline**

Create `src/minizen/core/pipeline.py`:

```python
import logging

import mistune

from minizen.ai.agent import DigestAgent
from minizen.config.models import Settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.rss.miniflux import MinifluxProvider

logger = logging.getLogger(__name__)


def run_pipeline(*, settings: Settings) -> None:
    rss = MinifluxProvider(config=settings.miniflux)
    email = EmailProvider(config=settings.email)
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)

    articles = rss.fetch_unread()
    if not articles:
        logger.info("No unread articles, nothing to do.")
        return

    result = agent.run(articles=articles)
    html = mistune.html(result.markdown)
    email.send(subject="Your daily digest", html=html)
    rss.mark_as_read(article_ids=result.articles_used)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/core/test_pipeline.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/core/pipeline.py tests/core/
git commit -m "feat: add core pipeline orchestration"
```

---

## Task 8: CLI — run command

**Files:**
- Create: `src/minizen/cli/__init__.py`
- Create: `src/minizen/cli/commands/__init__.py`
- Create: `src/minizen/cli/commands/run.py`
- Create: `tests/cli/__init__.py`
- Create: `tests/cli/test_run.py`

- [ ] **Step 1: Create empty init files and CLI app**

```bash
mkdir -p src/minizen/cli/commands tests/cli
touch tests/cli/__init__.py src/minizen/cli/commands/__init__.py
```

Create `src/minizen/cli/__init__.py`:

```python
import typer

app = typer.Typer(help="minizen — a quieter way to stay informed.")
```

- [ ] **Step 2: Write failing tests**

Create `tests/cli/test_run.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from minizen.cli import app


def test_run_command_calls_pipeline(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    mock_load = mocker.patch("minizen.cli.commands.run.load_settings", return_value=MagicMock())
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run", "--config", str(config_file)])

    # assert
    assert result.exit_code == 0
    mock_load.assert_called_once()
    mock_pipeline.assert_called_once_with(settings=mock_load.return_value)


def test_run_command_model_flag_overrides_settings(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    mock_settings = MagicMock()
    mock_load = mocker.patch("minizen.cli.commands.run.load_settings", return_value=mock_settings)
    mocker.patch("minizen.cli.commands.run.run_pipeline")
    runner = CliRunner()

    # act
    runner.invoke(app, ["run", "--config", str(config_file), "--model", "openai:gpt-4o"])

    # assert
    assert mock_settings.ai.model == "openai:gpt-4o"


def test_run_command_exits_nonzero_on_error(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    mocker.patch("minizen.cli.commands.run.load_settings", side_effect=KeyError("MINIFLUX_API_KEY"))
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run", "--config", str(config_file)])

    # assert
    assert result.exit_code != 0
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/cli/test_run.py -v
```

Expected: tests fail because the `run` command is not registered.

- [ ] **Step 4: Create the run command**

Create `src/minizen/cli/commands/run.py`:

```python
import logging
from pathlib import Path
from typing import Annotated

import typer

from minizen.config.loader import load_settings
from minizen.core.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def run(
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to config.toml.", envvar="MINIZEN_CONFIG"),
    ] = Path.home() / ".config" / "minizen" / "config.toml",
    model: Annotated[
        str | None,
        typer.Option("--model", help="Override the AI model for this run."),
    ] = None,
    log_level: Annotated[
        str,
        typer.Option("--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)."),
    ] = "INFO",
) -> None:
    """Fetch unread articles, summarise the highlights, and email the digest."""
    logging.basicConfig(level=log_level.upper())
    try:
        settings = load_settings(config_path=config)
        if model is not None:
            settings.ai.model = model
        run_pipeline(settings=settings)
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        raise typer.Exit(code=1) from exc
```

- [ ] **Step 5: Register the command in the CLI app**

Update `src/minizen/cli/__init__.py`:

```python
import typer

from minizen.cli.commands import run as run_module

app = typer.Typer(help="minizen — a quieter way to stay informed.")
app.command()(run_module.run)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_run.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/minizen/cli/ tests/cli/__init__.py tests/cli/test_run.py
git commit -m "feat: add CLI run command"
```

---

## Task 9: CLI — config commands

**Files:**
- Create: `src/minizen/cli/commands/config.py`
- Create: `tests/cli/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/cli/test_config.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import tomli_w
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from minizen.cli import app


def _write_config(path: Path) -> None:
    path.write_bytes(
        tomli_w.dumps(
            {
                "miniflux": {"url": "https://rss.example.com"},
                "email": {
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "from_addr": "from@example.com",
                    "to_addr": "to@example.com",
                },
                "ai": {"model": "anthropic:claude-sonnet-4-6", "top_n": 5},
            }
        ).encode()
    )


def test_config_show_prints_redacted_settings(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(config_file)
    mock_settings = MagicMock()
    mock_settings.miniflux.api_key = "secret"
    mock_settings.email.password = "secret"
    mocker.patch("minizen.cli.commands.config.load_settings", return_value=mock_settings)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "show", "--config", str(config_file)])

    # assert
    assert result.exit_code == 0
    assert "***" in result.output
    assert "secret" not in result.output


def test_config_validate_success(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(config_file)
    mock_settings = MagicMock()
    mock_settings.ai.model = "anthropic:claude-sonnet-4-6"
    mocker.patch("minizen.cli.commands.config.load_settings", return_value=mock_settings)
    mocker.patch("minizen.cli.commands.config.miniflux.Client")
    mocker.patch("minizen.cli.commands.config.smtplib.SMTP")
    mocker.patch("minizen.cli.commands.config.os.environ.get", return_value="key")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "validate", "--config", str(config_file)])

    # assert
    assert result.exit_code == 0
    assert "OK" in result.output


def test_config_set_updates_toml_value(tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(config_file)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app, ["config", "set", "ai.model", "openai:gpt-4o", "--config", str(config_file)]
    )

    # assert
    assert result.exit_code == 0
    import tomllib
    with open(config_file, "rb") as f:
        updated = tomllib.load(f)
    assert updated["ai"]["model"] == "openai:gpt-4o"


def test_config_set_rejects_unknown_key(tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(config_file)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app, ["config", "set", "nonexistent.key", "value", "--config", str(config_file)]
    )

    # assert
    assert result.exit_code != 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/cli/test_config.py -v
```

Expected: tests fail because the `config` subcommand is not registered.

- [ ] **Step 3: Create the config commands**

Create `src/minizen/cli/commands/config.py`:

```python
import os
import smtplib
import tomllib
from pathlib import Path
from typing import Annotated

import miniflux
import tomli_w
import typer

from minizen.config.loader import load_settings

config_app = typer.Typer(help="Manage minizen configuration.")

_CONFIG_OPTION = typer.Option(
    "--config",
    help="Path to config.toml.",
    envvar="MINIZEN_CONFIG",
)


def _default_config() -> Path:
    return Path.home() / ".config" / "minizen" / "config.toml"


@config_app.command("show")
def config_show(
    config: Annotated[Path, _CONFIG_OPTION] = _default_config(),
) -> None:
    """Print the resolved configuration with secrets redacted."""
    settings = load_settings(config_path=config)
    typer.echo(f"[miniflux]")
    typer.echo(f"  url       = {settings.miniflux.url}")
    typer.echo(f"  api_key   = ***")
    typer.echo(f"[email]")
    typer.echo(f"  smtp_host = {settings.email.smtp_host}")
    typer.echo(f"  smtp_port = {settings.email.smtp_port}")
    typer.echo(f"  from_addr = {settings.email.from_addr}")
    typer.echo(f"  to_addr   = {settings.email.to_addr}")
    typer.echo(f"  username  = {settings.email.username}")
    typer.echo(f"  password  = ***")
    typer.echo(f"[ai]")
    typer.echo(f"  model     = {settings.ai.model}")
    typer.echo(f"  top_n     = {settings.ai.top_n}")


@config_app.command("validate")
def config_validate(
    config: Annotated[Path, _CONFIG_OPTION] = _default_config(),
) -> None:
    """Test connections to Miniflux, SMTP, and AI provider."""
    settings = load_settings(config_path=config)
    errors: list[str] = []

    typer.echo("Checking Miniflux...", nl=False)
    try:
        miniflux.Client(
            base_url=settings.miniflux.url,
            api_key=settings.miniflux.api_key,
        ).get_me()
        typer.echo(" OK")
    except Exception as exc:
        typer.echo(f" FAIL ({exc})")
        errors.append("Miniflux")

    typer.echo("Checking SMTP...", nl=False)
    try:
        with smtplib.SMTP(host=settings.email.smtp_host, port=settings.email.smtp_port) as server:
            server.starttls()
            server.login(user=settings.email.username, password=settings.email.password)
        typer.echo(" OK")
    except Exception as exc:
        typer.echo(f" FAIL ({exc})")
        errors.append("SMTP")

    typer.echo("Checking AI provider...", nl=False)
    provider = settings.ai.model.split(":")[0]
    env_var = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(provider)
    if env_var and os.environ.get(env_var):
        typer.echo(" OK")
    else:
        typer.echo(f" FAIL (env var {env_var} not set)")
        errors.append("AI provider")

    if errors:
        typer.echo(f"\nFailed: {', '.join(errors)}")
        raise typer.Exit(code=1)


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Dot-separated key, e.g. ai.model")],
    value: Annotated[str, typer.Argument(help="New value")],
    config: Annotated[Path, _CONFIG_OPTION] = _default_config(),
) -> None:
    """Persist a configuration value to config.toml."""
    with open(config, "rb") as f:
        raw = tomllib.load(f)

    parts = key.split(".", maxsplit=1)
    if len(parts) != 2 or parts[0] not in raw or parts[1] not in raw[parts[0]]:
        typer.echo(f"Unknown key: {key}", err=True)
        raise typer.Exit(code=1)

    section, field = parts
    existing = raw[section][field]
    raw[section][field] = type(existing)(value)

    with open(config, "wb") as fb:
        fb.write(tomli_w.dumps(raw).encode())

    typer.echo(f"Set {key} = {raw[section][field]}")
```

- [ ] **Step 4: Register the config subapp in the CLI**

Update `src/minizen/cli/__init__.py`:

```python
import typer

from minizen.cli.commands import run as run_module
from minizen.cli.commands.config import config_app

app = typer.Typer(help="minizen — a quieter way to stay informed.")
app.command()(run_module.run)
app.add_typer(config_app, name="config")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_config.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/config.py src/minizen/cli/__init__.py tests/cli/test_config.py
git commit -m "feat: add CLI config commands"
```

---

## Task 10: CLI — digest commands

**Files:**
- Create: `src/minizen/cli/commands/digest.py`
- Create: `tests/cli/test_digest.py`

- [ ] **Step 1: Write failing tests**

Create `tests/cli/test_digest.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from minizen.ai.agent import DigestResult
from minizen.cli import app
from minizen.providers.rss.miniflux import Article
from datetime import datetime, timezone


def _make_article() -> Article:
    return Article(
        id=1,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=timezone.utc),
    )


def test_digest_preview_prints_markdown(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    mock_settings = MagicMock()
    mocker.patch("minizen.cli.commands.digest.load_settings", return_value=mock_settings)
    mock_rss = mocker.patch("minizen.cli.commands.digest.MinifluxProvider")
    mock_rss.return_value.fetch_unread.return_value = [_make_article()]
    mock_agent = mocker.patch("minizen.cli.commands.digest.DigestAgent")
    mock_agent.return_value.run.return_value = DigestResult(
        markdown="# Daily Digest\n\nSome news.", articles_used=[1]
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "preview", "--config", str(config_file)])

    # assert
    assert result.exit_code == 0
    assert "# Daily Digest" in result.output


def test_digest_preview_model_flag_overrides_settings(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    mock_settings = MagicMock()
    mocker.patch("minizen.cli.commands.digest.load_settings", return_value=mock_settings)
    mock_rss = mocker.patch("minizen.cli.commands.digest.MinifluxProvider")
    mock_rss.return_value.fetch_unread.return_value = [_make_article()]
    mock_agent = mocker.patch("minizen.cli.commands.digest.DigestAgent")
    mock_agent.return_value.run.return_value = DigestResult(
        markdown="# Digest", articles_used=[1]
    )
    runner = CliRunner()

    # act
    runner.invoke(
        app, ["digest", "preview", "--config", str(config_file), "--model", "openai:gpt-4o"]
    )

    # assert
    assert mock_settings.ai.model == "openai:gpt-4o"


def test_digest_send_test_sends_email(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    config_file.write_text("")
    mock_settings = MagicMock()
    mocker.patch("minizen.cli.commands.digest.load_settings", return_value=mock_settings)
    mock_email = mocker.patch("minizen.cli.commands.digest.EmailProvider")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "send-test", "--config", str(config_file)])

    # assert
    assert result.exit_code == 0
    mock_email.return_value.send.assert_called_once()
    call_kwargs = mock_email.return_value.send.call_args[1]
    assert "test" in call_kwargs["subject"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/cli/test_digest.py -v
```

Expected: tests fail because `digest` subcommand is not registered.

- [ ] **Step 3: Create the digest commands**

Create `src/minizen/cli/commands/digest.py`:

```python
from pathlib import Path
from typing import Annotated

import typer

from minizen.ai.agent import DigestAgent
from minizen.config.loader import load_settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.rss.miniflux import MinifluxProvider

digest_app = typer.Typer(help="Digest preview and testing commands.")

_CONFIG_OPTION = typer.Option(
    "--config",
    help="Path to config.toml.",
    envvar="MINIZEN_CONFIG",
)


def _default_config() -> Path:
    return Path.home() / ".config" / "minizen" / "config.toml"


@digest_app.command("preview")
def digest_preview(
    config: Annotated[Path, _CONFIG_OPTION] = _default_config(),
    model: Annotated[
        str | None,
        typer.Option("--model", help="Override the AI model for this run."),
    ] = None,
) -> None:
    """Fetch and summarise articles, print the digest to the terminal instead of emailing."""
    settings = load_settings(config_path=config)
    if model is not None:
        settings.ai.model = model

    rss = MinifluxProvider(config=settings.miniflux)
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)

    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return

    result = agent.run(articles=articles)
    typer.echo(result.markdown)


@digest_app.command("send-test")
def digest_send_test(
    config: Annotated[Path, _CONFIG_OPTION] = _default_config(),
) -> None:
    """Send a test email with dummy content to verify SMTP configuration."""
    settings = load_settings(config_path=config)
    email = EmailProvider(config=settings.email)
    email.send(
        subject="minizen test email",
        html="<h1>minizen test</h1><p>If you received this, SMTP is working correctly.</p>",
    )
    typer.echo("Test email sent successfully.")
```

- [ ] **Step 4: Register the digest subapp in the CLI**

Update `src/minizen/cli/__init__.py`:

```python
import typer

from minizen.cli.commands import run as run_module
from minizen.cli.commands.config import config_app
from minizen.cli.commands.digest import digest_app

app = typer.Typer(help="minizen — a quieter way to stay informed.")
app.command()(run_module.run)
app.add_typer(config_app, name="config")
app.add_typer(digest_app, name="digest")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_digest.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/digest.py src/minizen/cli/__init__.py tests/cli/test_digest.py
git commit -m "feat: add CLI digest commands"
```

---

## Task 11: CLI — setup wizard

**Files:**
- Create: `src/minizen/cli/commands/setup.py`
- Create: `tests/cli/test_setup.py`

- [ ] **Step 1: Write failing tests**

Create `tests/cli/test_setup.py`:

```python
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from minizen.cli import app


def test_setup_creates_config_file(tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    env_file = tmp_path / ".env"
    runner = CliRunner()
    inputs = "\n".join([
        "https://rss.example.com",  # miniflux url
        "mf-key",                   # miniflux api key
        "smtp.example.com",         # smtp host
        "587",                      # smtp port
        "from@example.com",         # from address
        "to@example.com",           # to address
        "email-user",               # smtp username
        "email-pass",               # smtp password
        "anthropic:claude-sonnet-4-6",  # ai model
        "5",                        # top_n
    ])

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_file), "--env-file", str(env_file)],
        input=inputs,
    )

    # assert
    assert result.exit_code == 0
    assert config_file.exists()
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    assert config["miniflux"]["url"] == "https://rss.example.com"
    assert config["email"]["smtp_host"] == "smtp.example.com"
    assert config["ai"]["model"] == "anthropic:claude-sonnet-4-6"
    assert config["ai"]["top_n"] == 5


def test_setup_creates_env_file_with_secrets(tmp_path: Path) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    env_file = tmp_path / ".env"
    runner = CliRunner()
    inputs = "\n".join([
        "https://rss.example.com",
        "mf-secret-key",
        "smtp.example.com",
        "587",
        "from@example.com",
        "to@example.com",
        "email-user",
        "email-pass",
        "anthropic:claude-sonnet-4-6",
        "5",
    ])

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_file), "--env-file", str(env_file)],
        input=inputs,
    )

    # assert
    assert env_file.exists()
    env_content = env_file.read_text()
    assert "MINIFLUX_API_KEY=mf-secret-key" in env_content
    assert "EMAIL_USERNAME=email-user" in env_content
    assert "EMAIL_PASSWORD=email-pass" in env_content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/cli/test_setup.py -v
```

Expected: tests fail because `setup` command is not registered.

- [ ] **Step 3: Create the setup wizard**

Create `src/minizen/cli/commands/setup.py`:

```python
from pathlib import Path
from typing import Annotated

import tomli_w
import typer


def setup(
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to write config.toml."),
    ] = Path.home() / ".config" / "minizen" / "config.toml",
    env_file: Annotated[
        Path,
        typer.Option("--env-file", help="Path to write .env file with secrets."),
    ] = Path(".env"),
) -> None:
    """Interactive setup wizard — generates config.toml and .env."""
    typer.echo("minizen setup wizard\n")

    miniflux_url = typer.prompt("Miniflux URL")
    miniflux_api_key = typer.prompt("Miniflux API key", hide_input=True)

    smtp_host = typer.prompt("SMTP host")
    smtp_port = int(typer.prompt("SMTP port", default="587"))
    from_addr = typer.prompt("From email address")
    to_addr = typer.prompt("To email address")
    email_username = typer.prompt("SMTP username")
    email_password = typer.prompt("SMTP password", hide_input=True)

    ai_model = typer.prompt("AI model", default="anthropic:claude-sonnet-4-6")
    top_n = int(typer.prompt("Number of top articles (top_n)", default="5"))

    config.parent.mkdir(parents=True, exist_ok=True)
    config_data = {
        "miniflux": {"url": miniflux_url},
        "email": {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "from_addr": from_addr,
            "to_addr": to_addr,
        },
        "ai": {"model": ai_model, "top_n": top_n},
    }
    with open(config, "wb") as f:
        f.write(tomli_w.dumps(config_data).encode())
    typer.echo(f"\nConfig written to {config}")

    provider = ai_model.split(":")[0]
    api_key_var = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(
        provider, "AI_API_KEY"
    )
    env_lines = [
        f"MINIFLUX_API_KEY={miniflux_api_key}",
        f"EMAIL_USERNAME={email_username}",
        f"EMAIL_PASSWORD={email_password}",
        f"{api_key_var}=<your-{provider}-api-key>",
    ]
    env_file.write_text("\n".join(env_lines) + "\n")
    typer.echo(f"Secrets template written to {env_file}")
    typer.echo(f"  → Set {api_key_var} in {env_file} before running minizen.\n")
    typer.echo("Setup complete. Run `minizen config validate` to test your connections.")
```

- [ ] **Step 4: Register the setup command in the CLI**

Update `src/minizen/cli/__init__.py`:

```python
import typer

from minizen.cli.commands import run as run_module
from minizen.cli.commands.config import config_app
from minizen.cli.commands.digest import digest_app
from minizen.cli.commands.setup import setup

app = typer.Typer(help="minizen — a quieter way to stay informed.")
app.command()(run_module.run)
app.command()(setup)
app.add_typer(config_app, name="config")
app.add_typer(digest_app, name="digest")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_setup.py -v
```

Expected: all 2 tests pass.

- [ ] **Step 6: Run the full test suite**

```bash
uv run pytest --cov=minizen --cov-report=term-missing --cov-fail-under=100 -v
```

Expected: all tests pass with 100% coverage.

- [ ] **Step 7: Run linters**

```bash
uv run ruff check && uv run ruff format --check
```

Expected: no errors. Fix any reported issues before committing.

- [ ] **Step 8: Commit**

```bash
git add src/minizen/cli/commands/setup.py src/minizen/cli/__init__.py tests/cli/test_setup.py
git commit -m "feat: add CLI setup wizard"
```

---

## Task 12: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/daily-digest.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create the workflow**

Create `.github/workflows/daily-digest.yml`:

```yaml
name: Daily digest

on:
  schedule:
    - cron: "0 8 * * *"  # 08:00 UTC every day
  workflow_dispatch:       # allow manual trigger

jobs:
  send-digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Run minizen
        run: uv run minizen run
        env:
          MINIFLUX_API_KEY: ${{ secrets.MINIFLUX_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          MINIZEN_CONFIG: ${{ github.workspace }}/config.toml
```

> **Note:** `config.toml` (without secrets) should be committed to the repository. The workflow uses `MINIZEN_CONFIG` to point to it. Add the file to the repo after running `minizen setup` locally, then remove the generated `.env` file from git tracking.

- [ ] **Step 3: Verify the workflow file passes zizmor**

```bash
uv run zizmor .github/workflows/daily-digest.yml --persona auditor
```

Expected: no security issues reported. If issues are found, fix them before committing.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/daily-digest.yml
git commit -m "ci: add daily digest GitHub Actions workflow"
```

---

## Final verification

- [ ] **Run the full test suite one last time**

```bash
uv run pytest --cov=minizen --cov-report=term-missing --cov-fail-under=100 -v
```

Expected: all tests pass, 100% coverage.

- [ ] **Verify the CLI help output**

```bash
uv run minizen --help
uv run minizen run --help
uv run minizen setup --help
uv run minizen config --help
uv run minizen digest --help
```

Expected: all commands are listed with correct descriptions.
