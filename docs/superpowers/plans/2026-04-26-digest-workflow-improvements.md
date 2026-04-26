# Digest Workflow Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the setup wizard bugs (missing miniflux section, prompt order, OpenAI support, .env permissions) and allow `minizen run` to work without a config file by accepting all settings as CLI flags.

**Architecture:** Four independent fix areas — (1) `config/loader.py` miniflux default, (2) `cli/commands/setup.py` prompt reorder + provider key logic + chmod, (3) `cli/commands/run.py` flag overrides + flag-only mode. Each area is covered by TDD before touching production code.

**Tech Stack:** Python 3.14, Pydantic v2 (`model_copy`), Typer, pytest, pytest-mock, tomllib/tomli-w.

---

## File Map

| File | Change |
|---|---|
| `src/minizen/config/loader.py` | Use `.get()` with default URL for missing `[miniflux]` section |
| `src/minizen/cli/commands/setup.py` | Add `_provider_key_info`, reorder prompts, write `[miniflux]` TOML section, chmod `.env` to 600, derive AI key var from model in non-interactive mode |
| `src/minizen/cli/commands/run.py` | Add `apply_overrides`, `_build_settings_from_flags`, and all credential flags |
| `tests/config/test_loader.py` | Add test: missing miniflux section → default URL |
| `tests/cli/commands/test_setup.py` | Update `_INTERACTIVE_INPUT` for new order; add tests for OpenAI, chmod, unknown provider |
| `tests/cli/commands/test_run.py` | Add tests for `apply_overrides`, flag-only mode, partial overrides |
| `docs/getting_started.md` | Update prompt table, add OpenAI key row, add "Run without config file" section |

---

## Task 1: Fix `load_settings` — missing miniflux section

**Files:**
- Modify: `src/minizen/config/loader.py`
- Test: `tests/config/test_loader.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/config/test_loader.py`:

```python
def test_load_settings_uses_default_miniflux_url_when_section_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "email-pass")

    # act
    settings = load_settings(config_path=config_file)

    # assert
    assert settings.miniflux.url == "https://reader.miniflux.app"
    assert settings.miniflux.api_key == "mf-key"
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/config/test_loader.py::test_load_settings_uses_default_miniflux_url_when_section_absent -v
```

Expected: `FAILED` — `KeyError: 'miniflux'`

- [ ] **Step 3: Implement the fix**

In `src/minizen/config/loader.py`, replace:

```python
        miniflux=MinifluxConfig(
            url=raw["miniflux"]["url"],
            api_key=os.environ["MINIFLUX_API_KEY"],
        ),
```

with:

```python
        miniflux=MinifluxConfig(
            url=raw.get("miniflux", {}).get("url", "https://reader.miniflux.app"),
            api_key=os.environ["MINIFLUX_API_KEY"],
        ),
```

- [ ] **Step 4: Run to verify it passes**

```bash
uv run pytest tests/config/test_loader.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/loader.py tests/config/test_loader.py
git commit -m "fix: default miniflux URL when section absent in config"
```

---

## Task 2: Write `[miniflux]` section in `_write_config`

**Files:**
- Modify: `src/minizen/cli/commands/setup.py`
- Test: `tests/cli/commands/test_setup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/cli/commands/test_setup.py`:

```python
def test_setup_writes_miniflux_section(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["miniflux"]["url"] == "https://reader.miniflux.app"
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/cli/commands/test_setup.py::test_setup_writes_miniflux_section -v
```

Expected: `FAILED` — `KeyError: 'miniflux'`

- [ ] **Step 3: Implement the fix**

In `src/minizen/cli/commands/setup.py`, in `_write_config`, update the `data` dict:

```python
    data = {
        "miniflux": {
            "url": "https://reader.miniflux.app",
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
```

- [ ] **Step 4: Run to verify it passes**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "fix: write miniflux section to config.toml in setup wizard"
```

---

## Task 3: Add `_provider_key_info` helper + reorder interactive prompts

**Files:**
- Modify: `src/minizen/cli/commands/setup.py`
- Test: `tests/cli/commands/test_setup.py`

The new prompt order is:
1. AI model
2. Number of top articles
3. SMTP host
4. SMTP port
5. From email address
6. To email address
7. Email username
8. Email password
9. Miniflux API key
10. AI provider API key (label from model)

- [ ] **Step 1: Update `_INTERACTIVE_INPUT` and existing tests**

In `tests/cli/commands/test_setup.py`, replace the module-level `_INTERACTIVE_INPUT` and update the `test_setup_accepts_custom_ai_values` input:

```python
_INTERACTIVE_INPUT = (
    "\n"                 # model (default: anthropic:claude-haiku-4-5)
    "\n"                 # top_n (default: 5)
    "\n"                 # smtp host (default: smtp.gmail.com)
    "\n"                 # smtp port (default: 587)
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    "email-password\n"
    "miniflux-api-key\n"
    "anthropic-api-key\n"
)
```

Update `test_setup_accepts_custom_ai_values` input:

```python
        input=(
            "openai:gpt-4o\n"
            "10\n"
            "\n"                  # smtp host (default)
            "\n"                  # smtp port (default)
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "openai-api-key\n"
        ),
```

- [ ] **Step 2: Add failing tests for new provider behaviour**

Add to `tests/cli/commands/test_setup.py`:

```python
def test_setup_writes_openai_key_for_openai_model(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "openai:gpt-4o\n"
            "\n"
            "\n"
            "\n"
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "openai-api-key\n"
        ),
    )

    # assert
    env_path = tmp_path / ".env"
    content = env_path.read_text()
    assert "OPENAI_API_KEY=openai-api-key" in content
    assert "ANTHROPIC_API_KEY" not in content


def test_setup_interactive_exits_on_unknown_model_provider(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "unknown:some-model\n"
            "\n"
            "\n"
            "\n"
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "some-api-key\n"
        ),
    )

    # assert
    assert result.exit_code != 0
    assert "Unknown model provider" in result.output
```

- [ ] **Step 3: Run to verify they fail**

```bash
uv run pytest tests/cli/commands/test_setup.py::test_setup_writes_openai_key_for_openai_model tests/cli/commands/test_setup.py::test_setup_interactive_exits_on_unknown_model_provider -v
```

Expected: `FAILED`

- [ ] **Step 4: Implement `_provider_key_info` and reorder prompts**

In `src/minizen/cli/commands/setup.py`, add the helper after `_DEFAULT_TOP_N`:

```python
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
```

Replace `_setup_interactive` body with the new prompt order:

```python
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

    resolved_model = typer.prompt("AI model", default=model or _DEFAULT_MODEL)
    resolved_top_n = typer.prompt(
        "Number of top articles", default=top_n or _DEFAULT_TOP_N
    )
    resolved_smtp_host = typer.prompt(
        "SMTP host", default=smtp_host or "smtp.gmail.com"
    )
    resolved_smtp_port = typer.prompt("SMTP port", default=smtp_port or 587)
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

    typer.echo(f"\nConfig written to:      {config}")
    typer.echo(f"Credentials written to: {env_path}")
```

- [ ] **Step 5: Run to verify all setup tests pass**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "feat: reorder setup prompts and add OpenAI provider support"
```

---

## Task 4: Add OpenAI support to non-interactive setup

**Files:**
- Modify: `src/minizen/cli/commands/setup.py`
- Test: `tests/cli/commands/test_setup.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/commands/test_setup.py`:

```python
def test_setup_non_interactive_accepts_openai_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config", str(config_path),
            "--from-addr", "from@example.com",
            "--to-addr", "to@example.com",
            "--model", "openai:gpt-4o",
        ],
    )

    # assert
    assert result.exit_code == 0


def test_setup_non_interactive_fails_with_unknown_model_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config", str(config_path),
            "--from-addr", "from@example.com",
            "--to-addr", "to@example.com",
            "--model", "unknown:some-model",
        ],
    )

    # assert
    assert result.exit_code != 0
    assert "Unknown model provider" in result.output
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run pytest tests/cli/commands/test_setup.py::test_setup_non_interactive_accepts_openai_model tests/cli/commands/test_setup.py::test_setup_non_interactive_fails_with_unknown_model_provider -v
```

Expected: `FAILED`

- [ ] **Step 3: Update `_setup_non_interactive`**

Replace the hardcoded `ANTHROPIC_API_KEY` check in `_setup_non_interactive`:

```python
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
```

- [ ] **Step 4: Run to verify all setup tests pass**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "feat: derive AI API key env var from model provider in non-interactive setup"
```

---

## Task 5: Set `.env` permissions to 600

**Files:**
- Modify: `src/minizen/cli/commands/setup.py`
- Test: `tests/cli/commands/test_setup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/cli/commands/test_setup.py`:

```python
def test_setup_sets_env_file_permissions(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    env_path = tmp_path / ".env"
    assert env_path.stat().st_mode & 0o777 == 0o600
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/cli/commands/test_setup.py::test_setup_sets_env_file_permissions -v
```

Expected: `FAILED` — permissions will be `0o644` or similar

- [ ] **Step 3: Add chmod after writing `.env`**

In `src/minizen/cli/commands/setup.py`, in `_setup_interactive`, add one line after `env_path.write_text(...)`:

```python
    env_path.write_text(
        f"MINIFLUX_API_KEY={miniflux_api_key}\n"
        f"{key_env_var}={ai_api_key}\n"
        f"MINIZEN_EMAIL_USERNAME={email_username}\n"
        f"MINIZEN_EMAIL_PASSWORD={email_password}\n"
    )
    env_path.chmod(0o600)
```

- [ ] **Step 4: Run to verify it passes**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "feat: set .env file permissions to 600 after writing"
```

---

## Task 6: Add `apply_overrides` and `_build_settings_from_flags` to `run.py`

**Files:**
- Modify: `src/minizen/cli/commands/run.py`
- Test: `tests/cli/commands/test_run.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/commands/test_run.py`:

```python
from minizen.cli.commands.run import apply_overrides, _build_settings_from_flags
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def _make_settings() -> Settings:
    return Settings(
        miniflux=MinifluxConfig(
            url="https://rss.example.com",
            api_key="old-mf-key",
        ),
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="from@example.com",
            to_addr="to@example.com",
            username="user",
            password="pass",
        ),
        ai=AIConfig(),
    )


def test_apply_overrides_replaces_miniflux_api_key() -> None:
    # arrange
    settings = _make_settings()

    # act
    result = apply_overrides(settings=settings, miniflux_api_key="new-mf-key")

    # assert
    assert result.miniflux.api_key == "new-mf-key"
    assert result.miniflux.url == "https://rss.example.com"


def test_apply_overrides_replaces_email_field() -> None:
    # arrange
    settings = _make_settings()

    # act
    result = apply_overrides(settings=settings, smtp_host="smtp.new.com", smtp_port=465)

    # assert
    assert result.email.smtp_host == "smtp.new.com"
    assert result.email.smtp_port == 465
    assert result.email.from_addr == "from@example.com"


def test_apply_overrides_ignores_none_values() -> None:
    # arrange
    settings = _make_settings()

    # act
    result = apply_overrides(settings=settings, miniflux_api_key=None, smtp_host=None)

    # assert
    assert result.miniflux.api_key == "old-mf-key"
    assert result.email.smtp_host == "smtp.example.com"


def test_build_settings_from_flags_succeeds_with_all_required() -> None:
    # act
    result = _build_settings_from_flags(
        miniflux_url=None,
        miniflux_api_key="mf-key",
        model=None,
        top_n=None,
        from_addr="from@example.com",
        to_addr="to@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        email_username="user",
        email_password="pass",
    )

    # assert
    assert result.miniflux.api_key == "mf-key"
    assert result.miniflux.url == "https://reader.miniflux.app"
    assert result.ai.model == "anthropic:claude-haiku-4-5"
    assert result.email.smtp_host == "smtp.example.com"


def test_build_settings_from_flags_exits_when_required_field_missing() -> None:
    # act / assert
    with pytest.raises(SystemExit):
        _build_settings_from_flags(
            miniflux_url=None,
            miniflux_api_key=None,
            model=None,
            top_n=None,
            from_addr="from@example.com",
            to_addr="to@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            email_username="user",
            email_password="pass",
        )
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run pytest tests/cli/commands/test_run.py::test_apply_overrides_replaces_miniflux_api_key tests/cli/commands/test_run.py::test_build_settings_from_flags_succeeds_with_all_required -v
```

Expected: `FAILED` — `ImportError`

- [ ] **Step 3: Implement `apply_overrides` and `_build_settings_from_flags`**

Add to `src/minizen/cli/commands/run.py` (after imports, before `run`):

```python
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings

_DEFAULT_MINIFLUX_URL = "https://reader.miniflux.app"
_DEFAULT_MODEL = "anthropic:claude-haiku-4-5"
_DEFAULT_TOP_N = 5


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
        k: v
        for k, v in {"model": model, "top_n": top_n}.items()
        if v is not None
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
        typer.echo(
            "Config file not found. Provide the following flags to run without a config file:"
        )
        for flag in missing:
            typer.echo(f"  {flag}")
        raise typer.Exit(code=1)

    return Settings(
        miniflux=MinifluxConfig(
            url=miniflux_url or _DEFAULT_MINIFLUX_URL,
            api_key=miniflux_api_key,  # type: ignore[arg-type]
        ),
        email=EmailConfig(
            smtp_host=smtp_host,  # type: ignore[arg-type]
            smtp_port=smtp_port,  # type: ignore[arg-type]
            from_addr=from_addr,  # type: ignore[arg-type]
            to_addr=to_addr,  # type: ignore[arg-type]
            username=email_username,  # type: ignore[arg-type]
            password=email_password,  # type: ignore[arg-type]
        ),
        ai=AIConfig(
            model=model or _DEFAULT_MODEL,
            top_n=top_n or _DEFAULT_TOP_N,
        ),
    )
```

- [ ] **Step 4: Run to verify tests pass**

```bash
uv run pytest tests/cli/commands/test_run.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/minizen/cli/commands/run.py tests/cli/commands/test_run.py
git commit -m "feat: add apply_overrides and _build_settings_from_flags helpers"
```

---

## Task 7: Add flags to `minizen run` and wire up override logic

**Files:**
- Modify: `src/minizen/cli/commands/run.py`
- Test: `tests/cli/commands/test_run.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/commands/test_run.py`:

```python
def test_run_flag_overrides_loaded_setting(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_settings = MagicMock()
    mock_settings.model_copy.return_value = mock_settings
    mock_settings.miniflux.model_copy.return_value = mock_settings.miniflux
    mock_settings.email.model_copy.return_value = mock_settings.email
    mock_settings.ai.model_copy.return_value = mock_settings.ai
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=mock_settings)
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "run",
            "--config", str(config_path),
            "--miniflux-api-key", "override-key",
        ],
    )

    # assert
    assert result.exit_code == 0
    mock_pipeline.assert_called_once()


def test_run_all_flags_no_config_file(mocker: MockerFixture) -> None:
    # arrange
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "run",
            "--config", "/nonexistent/config.toml",
            "--miniflux-api-key", "mf-key",
            "--from-addr", "from@example.com",
            "--to-addr", "to@example.com",
            "--smtp-host", "smtp.example.com",
            "--smtp-port", "587",
            "--email-username", "user",
            "--email-password", "pass",
        ],
    )

    # assert
    assert result.exit_code == 0
    called_settings = mock_pipeline.call_args.kwargs["settings"]
    assert called_settings.miniflux.api_key == "mf-key"
    assert called_settings.email.from_addr == "from@example.com"


def test_run_no_config_file_lists_missing_flags(mocker: MockerFixture) -> None:
    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["run", "--config", "/nonexistent/config.toml"],
    )

    # assert
    assert result.exit_code != 0
    assert "--miniflux-api-key" in result.output
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run pytest tests/cli/commands/test_run.py::test_run_all_flags_no_config_file tests/cli/commands/test_run.py::test_run_no_config_file_lists_missing_flags -v
```

Expected: `FAILED` — unknown option `--miniflux-api-key`

- [ ] **Step 3: Replace the `run` function in `run.py`**

```python
def run(
    config: Annotated[
        Path,
        typer.Option(help="Path to the TOML configuration file.", show_default=True),
    ] = _DEFAULT_CONFIG,
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
    _flag_kwargs = dict(
        miniflux_url=miniflux_url,
        miniflux_api_key=miniflux_api_key,
        model=model,
        top_n=top_n,
        from_addr=from_addr,
        to_addr=to_addr,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        email_username=email_username,
        email_password=email_password,
    )
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

- [ ] **Step 4: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/minizen/cli/commands/run.py tests/cli/commands/test_run.py
git commit -m "feat: add credential flags to minizen run for config-file-free operation"
```

---

## Task 8: Update documentation

**Files:**
- Modify: `docs/getting_started.md`

- [ ] **Step 1: Update the setup prompt table**

Replace the existing prompt table under `## Setup` with:

```markdown
| Prompt                  | Where to find it                                                        |
| ----------------------- | ----------------------------------------------------------------------- |
| **AI model**            | Model identifier, e.g. `anthropic:claude-haiku-4-5` or `openai:gpt-4o` |
| **Number of top articles** | How many articles to include in the digest (default: 5)              |
| **SMTP host**           | Your SMTP server hostname (e.g. `smtp.gmail.com`)                       |
| **SMTP port**           | SMTP port — use `587` for STARTTLS (works with most providers)          |
| **From email address**  | The address minizen sends from                                          |
| **To email address**    | Where you want to receive digests                                       |
| **Email username**      | Your SMTP login username (often your email address)                     |
| **Email password**      | Your SMTP password or app password (see your provider's docs)           |
| **Miniflux API key**    | Miniflux → Settings → API Keys → Create a new API key                   |
| **AI provider API key** | `ANTHROPIC_API_KEY` for Anthropic models; `OPENAI_API_KEY` for OpenAI  |
```

- [ ] **Step 2: Add "Run without a config file" section**

Add a new section after `## Run the full pipeline`:

```markdown
## Run without a config file

You can pass all credentials directly as flags — useful in CI/CD where you do not
want to store credentials on disk:

```bash
minizen run \
  --miniflux-api-key  "$MINIFLUX_API_KEY" \
  --from-addr         "digest@example.com" \
  --to-addr           "me@example.com" \
  --smtp-host         "smtp.gmail.com" \
  --smtp-port         587 \
  --email-username    "$EMAIL_USER" \
  --email-password    "$EMAIL_PASS"
```

Flags override the corresponding values in the config file when both are present.
```

- [ ] **Step 3: Update the GitHub Actions secrets list**

In the "Automate with GitHub Actions" section, replace:

```markdown
- `MINIFLUX_API_KEY`
- `ANTHROPIC_API_KEY`
- `MINIZEN_EMAIL_USERNAME`
- `MINIZEN_EMAIL_PASSWORD`
```

with:

```markdown
- `MINIFLUX_API_KEY`
- `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` if using an OpenAI model)
- `MINIZEN_EMAIL_USERNAME`
- `MINIZEN_EMAIL_PASSWORD`
```

- [ ] **Step 4: Commit**

```bash
git add docs/getting_started.md
git commit -m "docs: update getting started for OpenAI support and run flags"
```
