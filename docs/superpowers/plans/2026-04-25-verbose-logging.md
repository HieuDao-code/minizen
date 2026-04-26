# Verbose Logging Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `minizen digest fetch -v` (and `--verbose`) correctly enable DEBUG-level logging.

**Architecture:** Extract a shared `configure_logging(verbose)` helper into `src/minizen/cli/state.py` using `force=True` to override any pre-configured handlers. Add `verbose` as an explicit parameter to each `digest` subcommand (`fetch`, `preview`, `send-test`) so Typer parses the flag at the right command level. Update the root callback to call the shared helper.

**Tech Stack:** Python 3.14, Typer, standard `logging` module, pytest + pytest-mock.

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/minizen/cli/state.py` | **Create** | `configure_logging(verbose)` — shared logging setup with `force=True` |
| `src/minizen/cli/__init__.py` | **Modify** | Root callback imports and calls `configure_logging` instead of inline `basicConfig` |
| `src/minizen/cli/commands/digest.py` | **Modify** | Add `verbose` param + `configure_logging` call to `fetch`, `preview`, `send-test` |
| `tests/cli/test_state.py` | **Create** | Unit tests for `configure_logging` |
| `tests/cli/test_callback.py` | **Create** | Tests that root `-v` flag calls `configure_logging(True)` |
| `tests/cli/commands/test_digest.py` | **Modify** | Add tests that digest `-v` flag calls `configure_logging(True)` per command |

---

### Task 1: Create `configure_logging` with tests

**Files:**
- Create: `src/minizen/cli/state.py`
- Create: `tests/cli/test_state.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/cli/test_state.py`:

```python
import logging

import pytest
from pytest_mock import MockerFixture

from minizen.cli.state import configure_logging


def test_configure_logging_sets_debug_level(mocker: MockerFixture) -> None:
    # arrange
    mock_basicconfig = mocker.patch("minizen.cli.state.logging.basicConfig")

    # act
    configure_logging(verbose=True)

    # assert
    mock_basicconfig.assert_called_once_with(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
        force=True,
    )


def test_configure_logging_sets_info_level(mocker: MockerFixture) -> None:
    # arrange
    mock_basicconfig = mocker.patch("minizen.cli.state.logging.basicConfig")

    # act
    configure_logging(verbose=False)

    # assert
    mock_basicconfig.assert_called_once_with(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        force=True,
    )
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run pytest tests/cli/test_state.py -v
```

Expected: `ImportError: cannot import name 'configure_logging' from 'minizen.cli.state'`

- [ ] **Step 3: Create `src/minizen/cli/state.py`**

```python
import logging


def configure_logging(*, verbose: bool) -> None:
    """Configure the root logger for the CLI session.

    Args:
        verbose: When ``True``, sets the root logger to ``DEBUG`` level.
            When ``False``, sets it to ``INFO`` level.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        force=True,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_state.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/minizen/cli/state.py tests/cli/test_state.py
git commit -m "feat: add configure_logging helper with force=True"
```

---

### Task 2: Update root callback to use `configure_logging`

**Files:**
- Modify: `src/minizen/cli/__init__.py`
- Create: `tests/cli/test_callback.py`

- [ ] **Step 1: Write the failing test**

Create `tests/cli/test_callback.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from minizen.cli import app


def test_root_verbose_flag_calls_configure_logging(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.configure_logging")
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=MagicMock())
    mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    runner.invoke(app, ["-v", "run", "--config", str(config_path)])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


def test_root_no_verbose_flag_calls_configure_logging_false(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.configure_logging")
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=MagicMock())
    mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    runner.invoke(app, ["run", "--config", str(config_path)])

    # assert
    mock_configure.assert_called_once_with(verbose=False)
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run pytest tests/cli/test_callback.py -v
```

Expected: FAIL — `configure_logging` not yet imported into `minizen.cli`

- [ ] **Step 3: Update `src/minizen/cli/__init__.py`**

```python
import logging
from typing import Annotated

import typer

from minizen.cli.commands import (
    config as config_module,
    digest as digest_module,
)
from minizen.cli.commands.run import run
from minizen.cli.commands.setup import setup
from minizen.cli.state import configure_logging

app = typer.Typer(
    name="minizen",
    help="A quieter way to stay informed.",
    no_args_is_help=True,
)


@app.callback()
def _callback(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    """Configure logging for the CLI session."""
    configure_logging(verbose=verbose)


app.command("run")(run)
app.command("setup")(setup)
app.add_typer(config_module.app, name="config")
app.add_typer(digest_module.app, name="digest")
```

Note: remove the now-unused `import logging` line.

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_callback.py -v
```

Expected: 2 passed

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
uv run pytest tests/cli/ -v
```

Expected: all existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/__init__.py tests/cli/test_callback.py
git commit -m "feat: wire root callback to configure_logging helper"
```

---

### Task 3: Add `verbose` to digest subcommands

**Files:**
- Modify: `src/minizen/cli/commands/digest.py`
- Modify: `tests/cli/commands/test_digest.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/cli/commands/test_digest.py`:

```python
def test_digest_fetch_verbose_calls_configure_logging(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.commands.digest.configure_logging")
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=_make_settings_mock()
    )
    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "fetch", "-v"])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


def test_digest_preview_verbose_calls_configure_logging(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.commands.digest.configure_logging")
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=_make_settings_mock()
    )
    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "preview", "-v"])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


def test_digest_send_test_verbose_calls_configure_logging(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.commands.digest.configure_logging")
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=_make_settings_mock()
    )
    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "send-test", "-v"])

    # assert
    mock_configure.assert_called_once_with(verbose=True)
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run pytest tests/cli/commands/test_digest.py::test_digest_fetch_verbose_calls_configure_logging tests/cli/commands/test_digest.py::test_digest_preview_verbose_calls_configure_logging tests/cli/commands/test_digest.py::test_digest_send_test_verbose_calls_configure_logging -v
```

Expected: FAIL — `No such option: -v` on the fetch/preview/send-test commands

- [ ] **Step 3: Update `src/minizen/cli/commands/digest.py`**

```python
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from minizen.ai.agent import DigestAgent
from minizen.cli.state import configure_logging
from minizen.config.loader import load_settings
from minizen.config.models import Settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import MinifluxProvider

_DEFAULT_CONFIG = Path.home() / ".config" / "minizen" / "config.toml"

_CONFIG_OPTION = Annotated[
    Path,
    typer.Option(help="Path to the TOML configuration file.", show_default=True),
]

_VERBOSE_OPTION = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable debug logging."),
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
    config: _CONFIG_OPTION = _DEFAULT_CONFIG,
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
    config: _CONFIG_OPTION = _DEFAULT_CONFIG,
    verbose: _VERBOSE_OPTION = False,
) -> None:
    """Fetch and summarise articles, then print the Markdown digest."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    typer.echo(result.markdown)


@app.command("send-test")
def send_test(
    config: _CONFIG_OPTION = _DEFAULT_CONFIG,
    verbose: _VERBOSE_OPTION = False,
) -> None:
    """Send a test digest email without marking articles as read."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    html, plain_text = render_email(result.markdown)
    today = date.today().strftime("%B %-d, %Y")
    email = EmailProvider(config=settings.email)
    email.send(
        subject=f"[TEST] Your Daily Zen — {today}",
        html=html,
        plain_text=plain_text,
    )
    typer.echo("Test digest sent.")
```

- [ ] **Step 4: Run the new tests to verify they pass**

```bash
uv run pytest tests/cli/commands/test_digest.py::test_digest_fetch_verbose_calls_configure_logging tests/cli/commands/test_digest.py::test_digest_preview_verbose_calls_configure_logging tests/cli/commands/test_digest.py::test_digest_send_test_verbose_calls_configure_logging -v
```

Expected: 3 passed

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/digest.py tests/cli/commands/test_digest.py
git commit -m "feat: add --verbose/-v to digest subcommands"
```
