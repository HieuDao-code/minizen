# Documentation Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add missing module docstrings, consolidate duplicate default constants into `config/defaults.py`, and extend `docs/configuration.md` with a manual credential setup section.

**Architecture:** Three independent improvements applied sequentially — docstrings first (pure cosmetic, no tests needed), then constant extraction (refactor with existing test coverage), then docs update. The new `config/defaults.py` module becomes the single source of truth for all default values; CLI commands and config internals import from there rather than duplicating literals.

**Tech Stack:** Python 3.14, pydantic-ai, typer, pytest, ruff, ty

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Create | `src/minizen/config/defaults.py` | Single source of truth for all default constants |
| Create | `tests/config/test_defaults.py` | Verify default values |
| Modify | `src/minizen/main.py` | Add module docstring |
| Modify | `src/minizen/cli/__init__.py` | Add module docstring |
| Modify | `src/minizen/cli/state.py` | Add module docstring |
| Modify | `src/minizen/cli/commands/__init__.py` | Add module docstring |
| Modify | `src/minizen/cli/commands/config.py` | Add module docstring + use defaults |
| Modify | `src/minizen/cli/commands/digest.py` | Add module docstring + use defaults |
| Modify | `src/minizen/cli/commands/run.py` | Add module docstring + use defaults |
| Modify | `src/minizen/cli/commands/setup.py` | Add module docstring + use defaults |
| Modify | `src/minizen/config/models.py` | Use imported defaults as Pydantic field defaults |
| Modify | `src/minizen/config/loader.py` | Use `DEFAULT_MINIFLUX_URL` |
| Modify | `docs/configuration.md` | Add manual setup section |

---

### Task 1: Add module docstrings to CLI files

**Files:**
- Modify: `src/minizen/main.py`
- Modify: `src/minizen/cli/__init__.py`
- Modify: `src/minizen/cli/state.py`
- Modify: `src/minizen/cli/commands/__init__.py`
- Modify: `src/minizen/cli/commands/config.py`
- Modify: `src/minizen/cli/commands/digest.py`
- Modify: `src/minizen/cli/commands/run.py`
- Modify: `src/minizen/cli/commands/setup.py`

- [ ] **Step 1: Add module docstrings**

Add the following as the very first line of each file (before any imports):

`src/minizen/main.py`:
```python
"""Entry point for the minizen CLI application."""
```

`src/minizen/cli/__init__.py`:
```python
"""CLI application root — registers all sub-commands."""
```

`src/minizen/cli/state.py`:
```python
"""Shared CLI state and logging configuration."""
```

`src/minizen/cli/commands/__init__.py`:
```python
"""CLI command modules for the minizen application."""
```

`src/minizen/cli/commands/config.py`:
```python
"""CLI commands to inspect and update the minizen configuration."""
```

`src/minizen/cli/commands/digest.py`:
```python
"""CLI commands to preview or test the digest without sending."""
```

`src/minizen/cli/commands/run.py`:
```python
"""CLI command to run the full fetch-summarise-email pipeline."""
```

`src/minizen/cli/commands/setup.py`:
```python
"""Interactive and non-interactive setup wizard for minizen."""
```

- [ ] **Step 2: Run lint and type checks**

```bash
uv run ruff check && uv run ruff format --check && uv run ty check
```

Expected: no errors.

- [ ] **Step 3: Run tests**

```bash
uv run pytest
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/minizen/main.py src/minizen/cli/__init__.py src/minizen/cli/state.py src/minizen/cli/commands/__init__.py src/minizen/cli/commands/config.py src/minizen/cli/commands/digest.py src/minizen/cli/commands/run.py src/minizen/cli/commands/setup.py
git commit -m "docs: add module docstrings to CLI files"
```

---

### Task 2: Create `config/defaults.py`

**Files:**
- Create: `src/minizen/config/defaults.py`
- Create: `tests/config/test_defaults.py`

- [ ] **Step 1: Write the failing test**

Create `tests/config/test_defaults.py`:

```python
from pathlib import Path

from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_TOP_N,
)


def test_default_config_path() -> None:
    # act / assert
    assert DEFAULT_CONFIG_PATH == Path.home() / ".config" / "minizen" / "config.toml"


def test_default_miniflux_url() -> None:
    # act / assert
    assert DEFAULT_MINIFLUX_URL == "https://reader.miniflux.app"


def test_default_model() -> None:
    # act / assert
    assert DEFAULT_MODEL == "anthropic:claude-haiku-4-5"


def test_default_top_n() -> None:
    # act / assert
    assert DEFAULT_TOP_N == 5


def test_default_smtp_host() -> None:
    # act / assert
    assert DEFAULT_SMTP_HOST == "smtp.gmail.com"


def test_default_smtp_port() -> None:
    # act / assert
    assert DEFAULT_SMTP_PORT == 587
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/config/test_defaults.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'minizen.config.defaults'`

- [ ] **Step 3: Create `src/minizen/config/defaults.py`**

```python
"""Default values for all minizen configuration settings."""

from pathlib import Path

DEFAULT_CONFIG_PATH: Path = Path.home() / ".config" / "minizen" / "config.toml"
DEFAULT_MINIFLUX_URL: str = "https://reader.miniflux.app"
DEFAULT_MODEL: str = "anthropic:claude-haiku-4-5"
DEFAULT_TOP_N: int = 5
DEFAULT_SMTP_HOST: str = "smtp.gmail.com"
DEFAULT_SMTP_PORT: int = 587
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/config/test_defaults.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/defaults.py tests/config/test_defaults.py
git commit -m "feat: add config/defaults module as single source of truth for default values"
```

---

### Task 3: Update `config/models.py` to use defaults

**Files:**
- Modify: `src/minizen/config/models.py`
- Test: `tests/config/test_models.py` (existing — no changes needed)

- [ ] **Step 1: Update `config/models.py`**

Replace the file contents with:

```python
"""Pydantic settings models for the minizen configuration."""

from pydantic import BaseModel, Field

from minizen.config.defaults import (
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_TOP_N,
)


class MinifluxConfig(BaseModel):
    """Connection settings for the Miniflux RSS server."""

    url: str = Field(
        default=DEFAULT_MINIFLUX_URL,
        description="Base URL of the Miniflux instance (without /v1/ suffix).",
    )
    api_key: str = Field(description="Miniflux API key for authentication.")


class EmailConfig(BaseModel):
    """SMTP connection and addressing settings for outbound email."""

    smtp_host: str = Field(description="SMTP server hostname.")
    smtp_port: int = Field(description="SMTP server port (typically 587 for STARTTLS).")
    from_addr: str = Field(description="Sender email address.")
    to_addr: str = Field(description="Recipient email address.")
    username: str = Field(description="SMTP login username.")
    password: str = Field(description="SMTP login password or app password.")


class AIConfig(BaseModel):
    """AI model selection and digest size settings."""

    model: str = Field(
        default=DEFAULT_MODEL,
        description="pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).",  # noqa: E501
    )
    top_n: int = Field(
        default=DEFAULT_TOP_N,
        description="Maximum number of articles to include in the digest.",
    )


class Settings(BaseModel):
    """Top-level application settings composed from all sub-configs."""

    miniflux: MinifluxConfig = Field(description="Miniflux RSS server settings.")
    email: EmailConfig = Field(description="Email delivery settings.")
    ai: AIConfig = Field(description="AI model and digest size settings.")
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/config/ -v
```

Expected: all tests PASS (values unchanged — only source of truth moved).

- [ ] **Step 3: Commit**

```bash
git add src/minizen/config/models.py
git commit -m "refactor: use config.defaults constants in Pydantic models"
```

---

### Task 4: Update `config/loader.py` to use `DEFAULT_MINIFLUX_URL`

**Files:**
- Modify: `src/minizen/config/loader.py`
- Test: `tests/config/test_loader.py` (existing — no changes needed)

- [ ] **Step 1: Update `config/loader.py`**

Add the import and replace the hardcoded URL fallback. The full updated file:

```python
"""Settings loader — reads TOML config and overlays secrets from environment variables."""

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

from minizen.config.defaults import DEFAULT_MINIFLUX_URL
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def load_settings(*, config_path: Path) -> Settings:
    """Load application settings from a TOML config file and environment variables.

    Reads the TOML file at ``config_path``, then overlays secrets from the
    environment (with ``config_path.parent/.env`` taking precedence over the
    shell environment).

    Args:
        config_path: Path to the TOML configuration file.

    Returns:
        A fully populated ``Settings`` instance.

    Raises:
        FileNotFoundError: If ``config_path`` does not exist.
        KeyError: If a required environment variable is not set.
    """
    load_dotenv(config_path.parent / ".env")
    load_dotenv()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    ai_raw = raw.get("ai", {})

    return Settings(
        miniflux=MinifluxConfig(
            url=raw.get("miniflux", {}).get("url", DEFAULT_MINIFLUX_URL),
            api_key=os.environ["MINIFLUX_API_KEY"],
        ),
        email=EmailConfig(
            smtp_host=raw["email"]["smtp_host"],
            smtp_port=raw["email"]["smtp_port"],
            from_addr=raw["email"]["from_addr"],
            to_addr=raw["email"]["to_addr"],
            username=os.environ["MINIZEN_EMAIL_USERNAME"],
            password=os.environ["MINIZEN_EMAIL_PASSWORD"],
        ),
        ai=AIConfig(**ai_raw),
    )
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/config/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/minizen/config/loader.py
git commit -m "refactor: use DEFAULT_MINIFLUX_URL in config loader"
```

---

### Task 5: Update CLI commands to use defaults

**Files:**
- Modify: `src/minizen/cli/commands/config.py`
- Modify: `src/minizen/cli/commands/digest.py`
- Modify: `src/minizen/cli/commands/run.py`
- Modify: `src/minizen/cli/commands/setup.py`
- Test: `tests/cli/commands/test_config.py`, `test_digest.py`, `test_run.py`, `test_setup.py` (existing — no changes needed)

- [ ] **Step 1: Update `cli/commands/config.py`**

Replace the file contents with:

```python
"""CLI commands to inspect and update the minizen configuration."""

import contextlib
import tomllib
from pathlib import Path
from typing import Annotated

import tomli_w
import typer

from minizen.config.defaults import DEFAULT_CONFIG_PATH, DEFAULT_MODEL, DEFAULT_TOP_N
from minizen.config.loader import load_settings

_CONFIG_OPTION = Annotated[
    Path,
    typer.Option(help="Path to the TOML configuration file.", show_default=True),
]

app = typer.Typer(help="Inspect and update configuration.")


@app.command("show")
def show(config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH) -> None:
    """Display the current configuration."""
    try:
        with open(config, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)

    typer.echo(f"Config file: {config}")
    mf = data.get("miniflux", {})
    em = data.get("email", {})
    ai = data.get("ai", {})
    typer.echo(f"  miniflux.url:       {mf.get('url', '(unset)')}")
    typer.echo(f"  miniflux.api_key:   {'(from env)' if mf.get('url') else '(unset)'}")
    typer.echo(f"  email.smtp_host:    {em.get('smtp_host', '(unset)')}")
    typer.echo(f"  email.smtp_port:    {em.get('smtp_port', '(unset)')}")
    typer.echo(f"  email.from_addr:    {em.get('from_addr', '(unset)')}")
    typer.echo(f"  email.to_addr:      {em.get('to_addr', '(unset)')}")
    typer.echo(f"  ai.model:           {ai.get('model', DEFAULT_MODEL)}")
    typer.echo(f"  ai.top_n:           {ai.get('top_n', DEFAULT_TOP_N)}")


@app.command("validate")
def validate(config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH) -> None:
    """Validate the configuration file and environment variables."""
    try:
        load_settings(config_path=config)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)
    typer.echo("Configuration is valid.")


_ALLOWED_KEYS = {
    "miniflux.url",
    "ai.model",
    "ai.top_n",
    "email.smtp_host",
    "email.smtp_port",
    "email.from_addr",
    "email.to_addr",
}


@app.command("set")
def set_value(
    key: Annotated[
        str, typer.Argument(help="Dot-separated config key (e.g. ai.top_n).")
    ],
    value: Annotated[str, typer.Argument(help="New value.")],
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
) -> None:
    """Set a configuration value in the TOML file."""
    if key not in _ALLOWED_KEYS:
        allowed = ", ".join(sorted(_ALLOWED_KEYS))
        typer.echo(f"Error: unknown config key '{key}'. Allowed: {allowed}")
        raise typer.Exit(code=1)

    try:
        with open(config, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)

    section, field = key.split(".", 1)
    if section not in data:
        data[section] = {}

    # Coerce numeric strings to int
    coerced: str | int = value
    with contextlib.suppress(ValueError):
        coerced = int(value)

    data[section][field] = coerced
    config.write_bytes(tomli_w.dumps(data).encode())
    typer.echo(f"Set {key} = {coerced!r}")
```

- [ ] **Step 2: Update `cli/commands/digest.py`**

Replace the `_DEFAULT_CONFIG` definition and its usages. Full updated file:

```python
"""CLI commands to preview or test the digest without sending."""

from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from minizen.ai.agent import DigestAgent
from minizen.cli.state import configure_logging
from minizen.config.defaults import DEFAULT_CONFIG_PATH
from minizen.config.loader import load_settings
from minizen.config.models import Settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import MinifluxProvider

_CONFIG_OPTION = Annotated[
    Path,
    typer.Option(help="Path to the TOML configuration file.", show_default=True),
]

_VERBOSE_OPTION = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable debug logging."),
]

_DRY_RUN_OPTION = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Fetch articles but skip LLM call and any external sends.",
    ),
]

app = typer.Typer(help="Preview or test the digest without marking articles as read.")


def _load(config: Path) -> Settings:
    """Load settings from a TOML file, exiting with an error message on failure.

    Args:
        config: Path to the TOML configuration file.

    Returns:
        Fully loaded application settings.
    """
    try:
        return load_settings(config_path=config)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)


@app.command("fetch")
def fetch(
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
    verbose: _VERBOSE_OPTION = False,
) -> None:
    """Fetch unread articles and print their titles and URLs."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    typer.echo(f"{len(articles)} unread article(s):\n")
    for article in articles:
        typer.echo(f"[{article.feed_name}] {article.title}")
        typer.echo(f"  {article.url}")


@app.command("preview")
def preview(
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
    verbose: _VERBOSE_OPTION = False,
    dry_run: _DRY_RUN_OPTION = False,
) -> None:
    """Fetch and summarise articles, then print the Markdown digest."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    if dry_run:
        typer.echo(f"{len(articles)} unread article(s):\n")
        for article in articles:
            typer.echo(f"[{article.feed_name}] {article.title}")
            typer.echo(f"  {article.url}")
        return
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    typer.echo(result.markdown)


@app.command("send-test")
def send_test(
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
    verbose: _VERBOSE_OPTION = False,
    dry_run: _DRY_RUN_OPTION = False,
) -> None:
    """Send a test digest email without marking articles as read."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    if dry_run:
        typer.confirm(
            "This will make a real LLM API call but will not send an email. Continue?",
            abort=True,
        )
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    html, plain_text = render_email(result.markdown)
    if dry_run:
        typer.echo("Dry run — email not sent:\n")
        typer.echo(plain_text)
        return
    today = date.today().strftime("%B %-d, %Y")
    email = EmailProvider(config=settings.email)
    email.send(
        subject=f"[TEST] Your Daily Zen — {today}",
        html=html,
        plain_text=plain_text,
    )
    typer.echo("Test digest sent.")
```

- [ ] **Step 3: Update `cli/commands/run.py`**

Replace the module-level `_DEFAULT_*` constants with imports and use them throughout. Full updated file:

```python
"""CLI command to run the full fetch-summarise-email pipeline."""

from pathlib import Path
from typing import Annotated, cast

import typer

from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_TOP_N,
)
from minizen.config.loader import load_settings
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings
from minizen.core.pipeline import run_pipeline

_DRY_RUN_OPTION = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Fetch articles but skip LLM call, email send, and mark-as-read.",
    ),
]


def apply_overrides(
    settings: Settings,
    *,
    miniflux_url: str | None = None,
    miniflux_api_key: str | None = None,
    model: str | None = None,
    top_n: int | None = None,
    from_addr: str | None = None,
    to_addr: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    email_username: str | None = None,
    email_password: str | None = None,
) -> Settings:
    """Return a copy of settings with any non-None flag values applied.

    Args:
        settings: The base settings to override.
        miniflux_url: Override for miniflux.url.
        miniflux_api_key: Override for miniflux.api_key.
        model: Override for ai.model.
        top_n: Override for ai.top_n.
        from_addr: Override for email.from_addr.
        to_addr: Override for email.to_addr.
        smtp_host: Override for email.smtp_host.
        smtp_port: Override for email.smtp_port.
        email_username: Override for email.username.
        email_password: Override for email.password.

    Returns:
        A new Settings instance with overrides applied.
    """
    miniflux_updates = {
        k: v
        for k, v in {"url": miniflux_url, "api_key": miniflux_api_key}.items()
        if v is not None
    }
    ai_updates = {
        k: v for k, v in {"model": model, "top_n": top_n}.items() if v is not None
    }
    email_updates = {
        k: v
        for k, v in {
            "from_addr": from_addr,
            "to_addr": to_addr,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": email_username,
            "password": email_password,
        }.items()
        if v is not None
    }
    return settings.model_copy(
        deep=True,
        update={
            "miniflux": settings.miniflux.model_copy(update=miniflux_updates),
            "ai": settings.ai.model_copy(update=ai_updates),
            "email": settings.email.model_copy(update=email_updates),
        },
    )


def _build_settings_from_flags(
    *,
    miniflux_url: str | None,
    miniflux_api_key: str | None,
    model: str | None,
    top_n: int | None,
    from_addr: str | None,
    to_addr: str | None,
    smtp_host: str | None,
    smtp_port: int | None,
    email_username: str | None,
    email_password: str | None,
) -> Settings:
    """Build a Settings object entirely from CLI flags.

    Args:
        miniflux_url: Miniflux base URL (defaults to hosted instance if None).
        miniflux_api_key: Miniflux API key; required.
        model: AI model identifier (defaults to claude-haiku-4-5 if None).
        top_n: Max articles in digest (defaults to 5 if None).
        from_addr: Sender email address; required.
        to_addr: Recipient email address; required.
        smtp_host: SMTP server hostname; required.
        smtp_port: SMTP server port; required.
        email_username: SMTP login username; required.
        email_password: SMTP login password; required.

    Returns:
        A fully populated Settings instance.

    Raises:
        typer.Exit: With code 1 if any required field is absent.
    """
    required = {
        "--miniflux-api-key": miniflux_api_key,
        "--from-addr": from_addr,
        "--to-addr": to_addr,
        "--smtp-host": smtp_host,
        "--smtp-port": smtp_port,
        "--email-username": email_username,
        "--email-password": email_password,
    }
    missing = [flag for flag, value in required.items() if value is None]
    if missing:
        typer.echo("Config file not found. Required flags:")
        for flag in missing:
            typer.echo(f"  {flag}")
        raise typer.Exit(code=1)

    return Settings(
        miniflux=MinifluxConfig(
            url=miniflux_url or DEFAULT_MINIFLUX_URL,
            api_key=cast(str, miniflux_api_key),
        ),
        email=EmailConfig(
            smtp_host=cast(str, smtp_host),
            smtp_port=cast(int, smtp_port),
            from_addr=cast(str, from_addr),
            to_addr=cast(str, to_addr),
            username=cast(str, email_username),
            password=cast(str, email_password),
        ),
        ai=AIConfig(
            model=model or DEFAULT_MODEL,
            top_n=top_n or DEFAULT_TOP_N,
        ),
    )


def run(
    config: Annotated[
        Path,
        typer.Option(help="Path to the TOML configuration file.", show_default=True),
    ] = DEFAULT_CONFIG_PATH,
    dry_run: _DRY_RUN_OPTION = False,
    miniflux_url: Annotated[
        str | None,
        typer.Option("--miniflux-url", help="Miniflux base URL."),
    ] = None,
    miniflux_api_key: Annotated[
        str | None,
        typer.Option("--miniflux-api-key", help="Miniflux API key."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="AI model identifier."),
    ] = None,
    top_n: Annotated[
        int | None,
        typer.Option("--top-n", help="Number of top articles to include."),
    ] = None,
    from_addr: Annotated[
        str | None,
        typer.Option("--from-addr", help="Sender email address."),
    ] = None,
    to_addr: Annotated[
        str | None,
        typer.Option("--to-addr", help="Recipient email address."),
    ] = None,
    smtp_host: Annotated[
        str | None,
        typer.Option("--smtp-host", help="SMTP server hostname."),
    ] = None,
    smtp_port: Annotated[
        int | None,
        typer.Option("--smtp-port", help="SMTP server port."),
    ] = None,
    email_username: Annotated[
        str | None,
        typer.Option("--email-username", help="SMTP login username."),
    ] = None,
    email_password: Annotated[
        str | None,
        typer.Option("--email-password", help="SMTP login password."),
    ] = None,
) -> None:
    """Run the full digest pipeline: fetch, summarise, and email."""
    _flag_kwargs = {
        "miniflux_url": miniflux_url,
        "miniflux_api_key": miniflux_api_key,
        "model": model,
        "top_n": top_n,
        "from_addr": from_addr,
        "to_addr": to_addr,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "email_username": email_username,
        "email_password": email_password,
    }
    try:
        settings = load_settings(config_path=config)
    except FileNotFoundError:
        settings = _build_settings_from_flags(**_flag_kwargs)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)
    else:
        settings = apply_overrides(settings=settings, **_flag_kwargs)
    run_pipeline(settings=settings, dry_run=dry_run)
```

- [ ] **Step 4: Update `cli/commands/setup.py`**

Replace the module-level `_DEFAULT_*` constants with imports and use them throughout. Full updated file:

```python
"""Interactive and non-interactive setup wizard for minizen."""

import os
from pathlib import Path
from typing import Annotated

import tomli_w
import typer

from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_TOP_N,
)


def _provider_key_info(model: str) -> tuple[str, str]:
    """Return the prompt label and env var name for the AI provider API key.

    Args:
        model: pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).

    Returns:
        A tuple of (prompt_label, env_var_name).

    Raises:
        typer.Exit: If the model prefix is not a recognised provider.
    """
    if model.startswith("anthropic:"):
        return "Anthropic API key", "ANTHROPIC_API_KEY"
    if model.startswith("openai:"):
        return "OpenAI API key", "OPENAI_API_KEY"
    prefix = model.split(":")[0] if ":" in model else model
    typer.echo(f"Error: Unknown model provider: {prefix}")
    raise typer.Exit(code=1)


def setup(
    config: Annotated[
        Path,
        typer.Option(help="Path to write the TOML configuration file."),
    ] = DEFAULT_CONFIG_PATH,
    no_interactive: Annotated[
        bool,
        typer.Option(
            "--no-interactive", help="Skip prompts; read secrets from env vars."
        ),
    ] = False,
    from_addr: Annotated[
        str | None,
        typer.Option("--from-addr", help="From email address."),
    ] = None,
    to_addr: Annotated[
        str | None,
        typer.Option("--to-addr", help="To email address."),
    ] = None,
    smtp_host: Annotated[
        str | None,
        typer.Option("--smtp-host", help="SMTP host."),
    ] = None,
    smtp_port: Annotated[
        int | None,
        typer.Option("--smtp-port", help="SMTP port."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="AI model identifier."),
    ] = None,
    top_n: Annotated[
        int | None,
        typer.Option("--top-n", help="Number of top articles to include."),
    ] = None,
) -> None:
    """Interactive wizard to create a minizen configuration file."""
    if no_interactive:
        _setup_non_interactive(
            config=config,
            from_addr=from_addr,
            to_addr=to_addr,
            smtp_host=smtp_host or DEFAULT_SMTP_HOST,
            smtp_port=smtp_port or DEFAULT_SMTP_PORT,
            model=model or DEFAULT_MODEL,
            top_n=top_n or DEFAULT_TOP_N,
        )
    else:
        _setup_interactive(
            config=config,
            from_addr=from_addr,
            to_addr=to_addr,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            model=model,
            top_n=top_n,
        )


def _setup_non_interactive(
    *,
    config: Path,
    from_addr: str | None,
    to_addr: str | None,
    smtp_host: str,
    smtp_port: int,
    model: str,
    top_n: int,
) -> None:
    """Write config non-interactively, reading secrets from environment variables.

    Args:
        config: Destination path for the TOML config file.
        from_addr: Sender email address; required, exits with code 1 if absent.
        to_addr: Recipient email address; required, exits with code 1 if absent.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        model: AI model identifier.
        top_n: Number of top articles to include in the digest.
    """
    if not from_addr:
        typer.echo("Error: --from-addr is required in non-interactive mode.")
        raise typer.Exit(code=1)
    if not to_addr:
        typer.echo("Error: --to-addr is required in non-interactive mode.")
        raise typer.Exit(code=1)

    _, ai_key_var = _provider_key_info(model)

    for var in (
        "MINIFLUX_API_KEY",
        ai_key_var,
        "MINIZEN_EMAIL_USERNAME",
        "MINIZEN_EMAIL_PASSWORD",
    ):
        if not os.environ.get(var):
            typer.echo(f"Error: environment variable {var} is not set.")
            raise typer.Exit(code=1)

    _write_config(
        config=config,
        from_addr=from_addr,
        to_addr=to_addr,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        model=model,
        top_n=top_n,
    )
    typer.echo(f"Config written to: {config}")


def _setup_interactive(
    *,
    config: Path,
    from_addr: str | None,
    to_addr: str | None,
    smtp_host: str | None,
    smtp_port: int | None,
    model: str | None,
    top_n: int | None,
) -> None:
    """Prompt the user for all settings interactively, then write config and .env.

    Args:
        config: Destination path for the TOML config file.
        from_addr: Pre-filled sender address (used as default prompt value).
        to_addr: Pre-filled recipient address (used as default prompt value).
        smtp_host: Pre-filled SMTP host (used as default prompt value).
        smtp_port: Pre-filled SMTP port (used as default prompt value).
        model: Pre-filled AI model identifier (used as default prompt value).
        top_n: Pre-filled article count (used as default prompt value).
    """
    typer.echo("minizen setup wizard")
    typer.echo("--------------------")

    resolved_model = typer.prompt("AI model", default=model or DEFAULT_MODEL)
    resolved_top_n = typer.prompt(
        "Number of top articles", default=top_n or DEFAULT_TOP_N
    )
    resolved_smtp_host = typer.prompt(
        "SMTP host", default=smtp_host or DEFAULT_SMTP_HOST
    )
    resolved_smtp_port = typer.prompt("SMTP port", default=smtp_port or DEFAULT_SMTP_PORT)
    resolved_from_addr = typer.prompt("From email address", default=from_addr or "")
    resolved_to_addr = typer.prompt("To email address", default=to_addr or "")
    email_username = typer.prompt("Email username (SMTP login)")
    email_password = typer.prompt("Email password (App Password)", hide_input=True)
    miniflux_api_key = typer.prompt("Miniflux API key", hide_input=True)

    key_label, key_env_var = _provider_key_info(resolved_model)
    ai_api_key = typer.prompt(key_label, hide_input=True)

    _write_config(
        config=config,
        from_addr=resolved_from_addr,
        to_addr=resolved_to_addr,
        smtp_host=resolved_smtp_host,
        smtp_port=int(resolved_smtp_port),
        model=resolved_model,
        top_n=int(resolved_top_n),
    )

    env_path = config.parent / ".env"
    env_path.write_text(
        f"MINIFLUX_API_KEY={miniflux_api_key}\n"
        f"{key_env_var}={ai_api_key}\n"
        f"MINIZEN_EMAIL_USERNAME={email_username}\n"
        f"MINIZEN_EMAIL_PASSWORD={email_password}\n"
    )
    env_path.chmod(0o600)

    typer.echo(f"\nConfig written to:      {config}")
    typer.echo(f"Credentials written to: {env_path}")


def _write_config(
    *,
    config: Path,
    from_addr: str,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    model: str,
    top_n: int,
) -> None:
    """Serialise the given settings to a TOML file, creating parent directories.

    Args:
        config: Destination path for the TOML config file.
        from_addr: Sender email address.
        to_addr: Recipient email address.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        model: AI model identifier.
        top_n: Number of top articles to include in the digest.
    """
    data = {
        "miniflux": {
            "url": DEFAULT_MINIFLUX_URL,
        },
        "email": {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "from_addr": from_addr,
            "to_addr": to_addr,
        },
        "ai": {
            "model": model,
            "top_n": top_n,
        },
    }
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(tomli_w.dumps(data).encode())
```

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest
```

Expected: all tests PASS.

- [ ] **Step 6: Run lint and type checks**

```bash
uv run ruff check && uv run ruff format --check && uv run ty check
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add src/minizen/cli/commands/config.py src/minizen/cli/commands/digest.py src/minizen/cli/commands/run.py src/minizen/cli/commands/setup.py
git commit -m "refactor: use config.defaults constants in CLI commands"
```

---

### Task 6: Add manual setup section to `docs/configuration.md`

**Files:**
- Modify: `docs/configuration.md`

- [ ] **Step 1: Append the manual setup section**

Add the following to the end of `docs/configuration.md`:

```markdown
---

## Manual setup (without `minizen setup`)

You can configure minizen entirely by hand — no wizard required.

### 1. Create the config file

Copy this template to `~/.config/minizen/config.toml` and fill in your values:

```toml
[miniflux]
url = "https://reader.miniflux.app"  # or your self-hosted URL

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
from_addr = "you@example.com"
to_addr = "you@example.com"

[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
```

Use `minizen config set` to update individual values later:

```bash
minizen config set ai.top_n 10
minizen config set ai.model "openai:gpt-4o-mini"
```

### 2. Set secrets via `.env` file

Create `~/.config/minizen/.env` (same directory as `config.toml`):

```dotenv
MINIFLUX_API_KEY=your-miniflux-api-key
ANTHROPIC_API_KEY=your-anthropic-key   # or OPENAI_API_KEY
MINIZEN_EMAIL_USERNAME=your-smtp-username
MINIZEN_EMAIL_PASSWORD=your-smtp-app-password
```

Restrict permissions so only your user can read it:

```bash
chmod 600 ~/.config/minizen/.env
```

### 3. Set secrets via shell rc file

As an alternative to `.env`, export the variables in your shell profile
(`~/.bashrc`, `~/.zshrc`, or equivalent):

```bash
export MINIFLUX_API_KEY="your-miniflux-api-key"
export ANTHROPIC_API_KEY="your-anthropic-key"   # or OPENAI_API_KEY
export MINIZEN_EMAIL_USERNAME="your-smtp-username"
export MINIZEN_EMAIL_PASSWORD="your-smtp-app-password"
```

Reload your shell after editing: `source ~/.zshrc` (or `source ~/.bashrc`).

### 4. Verify the setup

```bash
minizen config validate
```

A clean output confirms minizen can read all required values.
```

- [ ] **Step 2: Commit**

```bash
git add docs/configuration.md
git commit -m "docs: add manual credential setup section to configuration reference"
```
