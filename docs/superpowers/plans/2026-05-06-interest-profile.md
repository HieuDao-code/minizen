# Interest Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `interests` and `avoid` lists to the AI config so the agent prioritises articles the user cares about and skips topics they don't want.

**Architecture:** Two optional `list[str]` fields are added to `AIConfig`. `DigestAgent` builds its system prompt dynamically — appending a preference block only when at least one list is non-empty. The setup wizard gains two skippable prompts (and two `--interests`/`--avoid` CLI flags) that write the lists to the TOML config.

**Tech Stack:** pydantic `Field`, `pydantic-ai` `Agent`, `typer`, `tomli_w`

---

### Task 1: Add `interests` and `avoid` to `AIConfig`

**Files:**
- Modify: `src/minizen/config/models.py`
- Test: `tests/config/test_models.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/config/test_models.py`:

```python
def test_ai_config_defaults_interests_and_avoid_to_empty_lists() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.interests == []
    assert config.avoid == []


def test_ai_config_accepts_interests_and_avoid() -> None:
    # act
    config = AIConfig(
        interests=["Rust", "AI safety"],
        avoid=["sports", "crypto"],
    )

    # assert
    assert config.interests == ["Rust", "AI safety"]
    assert config.avoid == ["sports", "crypto"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/config/test_models.py::test_ai_config_defaults_interests_and_avoid_to_empty_lists tests/config/test_models.py::test_ai_config_accepts_interests_and_avoid -v
```

Expected: FAIL with `unexpected keyword argument`

- [ ] **Step 3: Add the fields to `AIConfig`**

In `src/minizen/config/models.py`, update `AIConfig`:

```python
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
    max_words_per_article: int = Field(
        default=500,
        description="Maximum words of article content sent to the LLM per article.",
    )
    interests: list[str] = Field(
        default_factory=list,
        description="Topics to prioritise when selecting articles.",
    )
    avoid: list[str] = Field(
        default_factory=list,
        description="Topics to avoid when selecting articles.",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/config/test_models.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/models.py tests/config/test_models.py
git commit -m "feat: add interests and avoid fields to AIConfig"
```

---

### Task 2: Inject preference block into `DigestAgent` system prompt

**Files:**
- Modify: `src/minizen/ai/agent.py`
- Test: `tests/ai/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/ai/test_agent.py`:

```python
def test_agent_initialized_with_preference_block_when_interests_set(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        interests=["Rust", "AI safety"],
        avoid=[],
    )

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert "Prioritise articles about: Rust, AI safety" in call_kwargs["system_prompt"]


def test_agent_initialized_with_preference_block_when_avoid_set(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        interests=[],
        avoid=["sports", "crypto"],
    )

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert "Avoid articles about: sports, crypto" in call_kwargs["system_prompt"]


def test_agent_uses_base_system_prompt_when_no_preferences(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=5)

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert call_kwargs["system_prompt"] == _SYSTEM_PROMPT
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/ai/test_agent.py::test_agent_initialized_with_preference_block_when_interests_set tests/ai/test_agent.py::test_agent_initialized_with_preference_block_when_avoid_set tests/ai/test_agent.py::test_agent_uses_base_system_prompt_when_no_preferences -v
```

Expected: FAIL with `unexpected keyword argument 'interests'`

- [ ] **Step 3: Add `_build_system_prompt` and update `DigestAgent`**

In `src/minizen/ai/agent.py`, add this function after `_SYSTEM_PROMPT`:

```python
def _build_system_prompt(*, interests: list[str], avoid: list[str]) -> str:
    """Build the system prompt, appending a user-preference block when non-empty.

    Args:
        interests: Topics the user wants to prioritise.
        avoid: Topics the user wants to exclude.

    Returns:
        The base system prompt unchanged when both lists are empty, or with a
        ``User preferences:`` block appended when at least one list is non-empty.
    """
    if not interests and not avoid:
        return _SYSTEM_PROMPT
    lines = ["User preferences:"]
    if interests:
        lines.append(f"- Prioritise articles about: {', '.join(interests)}")
    if avoid:
        lines.append(f"- Avoid articles about: {', '.join(avoid)}")
    return _SYSTEM_PROMPT + "\n" + "\n".join(lines) + "\n"
```

Then update `DigestAgent.__init__`:

```python
def __init__(
    self,
    *,
    model: str,
    top_n: int,
    max_words_per_article: int = 500,
    interests: list[str] | None = None,
    avoid: list[str] | None = None,
) -> None:
    """Initialise the agent with the given model and digest settings.

    Args:
        model: pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).
        top_n: Maximum number of articles to include in the digest.
        max_words_per_article: Maximum words of article content sent to the
            LLM per article.
        interests: Topics to prioritise when selecting articles.
        avoid: Topics to exclude when selecting articles.
    """
    logger.debug(
        "Initialising DigestAgent: model=%s, top_n=%d, max_words=%d",
        model,
        top_n,
        max_words_per_article,
    )
    self._top_n = top_n
    self._max_words_per_article = max_words_per_article
    system_prompt = _build_system_prompt(
        interests=interests or [],
        avoid=avoid or [],
    )
    self._agent = Agent(
        model=model,
        output_type=DigestResult,
        system_prompt=system_prompt,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat: inject interest-profile preference block into DigestAgent system prompt"
```

---

### Task 3: Wire interests/avoid through the pipeline

**Files:**
- Modify: `src/minizen/core/pipeline.py`
- Test: `tests/core/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/core/test_pipeline.py` and update the existing `test_pipeline_runs_full_flow` assertion:

First, update `_make_settings()` to create a helper that accepts optional interests/avoid:

```python
def _make_settings(
    *,
    interests: list[str] | None = None,
    avoid: list[str] | None = None,
) -> Settings:
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
        ai=AIConfig(
            model="anthropic:claude-sonnet-4-6",
            top_n=2,
            interests=interests or [],
            avoid=avoid or [],
        ),
    )
```

Update the `mock_agent_cls.assert_called_once_with` assertion in `test_pipeline_runs_full_flow` to include the new params:

```python
mock_agent_cls.assert_called_once_with(
    model="anthropic:claude-sonnet-4-6",
    top_n=2,
    max_words_per_article=500,
    interests=[],
    avoid=[],
)
```

Then add a new test:

```python
@freeze_time("2026-04-29")
def test_pipeline_passes_interests_and_avoid_to_agent(
    mocker: MockerFixture,
) -> None:
    # arrange
    articles = [_make_article(1)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_email = MagicMock()
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mock_agent_cls = mocker.patch(
        "minizen.core.pipeline.DigestAgent", return_value=mock_agent
    )
    mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    settings = _make_settings(interests=["Rust", "AI"], avoid=["sports"])

    # act
    run_pipeline(settings=settings)

    # assert
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=2,
        max_words_per_article=500,
        interests=["Rust", "AI"],
        avoid=["sports"],
    )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/core/test_pipeline.py::test_pipeline_runs_full_flow tests/core/test_pipeline.py::test_pipeline_passes_interests_and_avoid_to_agent -v
```

Expected: `test_pipeline_runs_full_flow` FAIL (assert mismatch on DigestAgent call), new test FAIL

- [ ] **Step 3: Update `run_pipeline` to pass interests and avoid**

In `src/minizen/core/pipeline.py`, update the `DigestAgent` construction:

```python
agent = DigestAgent(
    model=settings.ai.model,
    top_n=settings.ai.top_n,
    max_words_per_article=settings.ai.max_words_per_article,
    interests=settings.ai.interests,
    avoid=settings.ai.avoid,
)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/core/test_pipeline.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/minizen/core/pipeline.py tests/core/test_pipeline.py
git commit -m "feat: pass interests and avoid from settings through to DigestAgent"
```

---

### Task 4: Add wizard prompts and `--interests`/`--avoid` CLI flags

**Files:**
- Modify: `src/minizen/cli/commands/setup.py`
- Test: `tests/cli/commands/test_setup.py`

- [ ] **Step 1: Write the failing tests**

Update `_INTERACTIVE_INPUT` in `tests/cli/commands/test_setup.py` to include two `\n` skips after `top_n`:

```python
_INTERACTIVE_INPUT = (
    "\n"  # model (default: anthropic:claude-haiku-4-5)
    "\n"  # top_n (default: 10)
    "\n"  # interests (skip)
    "\n"  # avoid (skip)
    "\n"  # smtp host (default: smtp.gmail.com)
    "\n"  # smtp port (default: 587)
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    "email-password\n"
    "miniflux-api-key\n"
    "anthropic-api-key\n"
)
```

Also update these existing test inputs that inline their own input strings (add `"\n"  # interests (skip)\n"\n"  # avoid (skip)\n` after the `top_n` line in each):

- `test_setup_accepts_custom_ai_values`:
```python
input=(
    "openai:gpt-4o\n"
    "10\n"
    "\n"  # interests (skip)
    "\n"  # avoid (skip)
    "\n"  # smtp host (default)
    "\n"  # smtp port (default)
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    "email-password\n"
    "miniflux-api-key\n"
    "openai-api-key\n"
),
```

- `test_setup_writes_openai_key_for_openai_model`:
```python
input=(
    "openai:gpt-4o\n"
    "\n"
    "\n"  # interests (skip)
    "\n"  # avoid (skip)
    "\n"
    "\n"
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    "email-password\n"
    "miniflux-api-key\n"
    "openai-api-key\n"
),
```

- `test_setup_interactive_exits_on_unknown_model_provider`:
```python
input=(
    "unknown:some-model\n"
    "\n"
    "\n"  # interests (skip)
    "\n"  # avoid (skip)
    "\n"
    "\n"
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    "email-password\n"
    "miniflux-api-key\n"
    "some-api-key\n"
),
```

- `test_setup_quotes_env_values_with_special_chars`:
```python
input=(
    "\n"  # model (default)
    "\n"  # top_n (default)
    "\n"  # interests (skip)
    "\n"  # avoid (skip)
    "\n"  # smtp host (default)
    "\n"  # smtp port (default)
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    'p@ss"word\n'
    "miniflux-api-key\n"
    "anthropic-api-key\n"
),
```

Then add new tests:

```python
def test_setup_interactive_writes_interests_and_avoid(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "\n"  # model (default)
            "\n"  # top_n (default)
            "Rust, AI safety\n"
            "sports, crypto\n"
            "\n"  # smtp host (default)
            "\n"  # smtp port (default)
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "anthropic-api-key\n"
        ),
    )

    # assert
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    assert data["ai"]["interests"] == ["Rust", "AI safety"]
    assert data["ai"]["avoid"] == ["sports", "crypto"]


def test_setup_interactive_skipped_interests_omitted_from_config(
    tmp_path: Path,
) -> None:
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
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    assert "interests" not in data["ai"]
    assert "avoid" not in data["ai"]


def test_setup_non_interactive_writes_interests_and_avoid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
            "--interests",
            "Rust,AI safety",
            "--avoid",
            "sports,crypto",
        ],
    )

    # assert
    assert result.exit_code == 0
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    assert data["ai"]["interests"] == ["Rust", "AI safety"]
    assert data["ai"]["avoid"] == ["sports", "crypto"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: multiple FAILs — existing tests fail because `_INTERACTIVE_INPUT` is wrong, new tests fail because the wizard doesn't have the new prompts yet.

- [ ] **Step 3: Update `setup.py`**

Replace the full contents of `src/minizen/cli/commands/setup.py` with:

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
    prefix = model.split(":", maxsplit=1)[0] if ":" in model else model
    typer.echo(f"Error: Unknown model provider: {prefix}")
    raise typer.Exit(code=1)


def _parse_comma_list(value: str | None) -> list[str]:
    """Split a comma-separated string into a stripped list, dropping empty items.

    Args:
        value: Raw comma-separated string, or ``None``.

    Returns:
        List of stripped non-empty strings. Returns ``[]`` for ``None`` or blank input.
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


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
    interests: Annotated[
        str | None,
        typer.Option("--interests", help="Comma-separated topics to prioritise."),
    ] = None,
    avoid: Annotated[
        str | None,
        typer.Option("--avoid", help="Comma-separated topics to avoid."),
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
            interests=_parse_comma_list(interests),
            avoid=_parse_comma_list(avoid),
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
            interests=interests,
            avoid=avoid,
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
    interests: list[str],
    avoid: list[str],
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
        interests: Topics to prioritise when selecting articles.
        avoid: Topics to exclude when selecting articles.
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
        interests=interests,
        avoid=avoid,
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
    interests: str | None,
    avoid: str | None,
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
        interests: Pre-filled interests string (used as default prompt value).
        avoid: Pre-filled avoid string (used as default prompt value).
    """
    typer.echo("minizen setup wizard")
    typer.echo("--------------------")

    resolved_model = typer.prompt("AI model", default=model or DEFAULT_MODEL)
    resolved_top_n = typer.prompt(
        "Number of top articles", default=top_n or DEFAULT_TOP_N
    )
    interests_str = typer.prompt(
        "Topics to prioritise (comma-separated, Enter to skip)",
        default=interests or "",
    )
    avoid_str = typer.prompt(
        "Topics to avoid (comma-separated, Enter to skip)",
        default=avoid or "",
    )
    resolved_smtp_host = typer.prompt(
        "SMTP host", default=smtp_host or DEFAULT_SMTP_HOST
    )
    resolved_smtp_port = typer.prompt(
        "SMTP port", default=smtp_port or DEFAULT_SMTP_PORT
    )
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
        interests=_parse_comma_list(interests_str),
        avoid=_parse_comma_list(avoid_str),
    )

    env_path = config.parent / ".env"
    env_path.write_text(
        f"MINIFLUX_API_KEY={_quote_env_value(miniflux_api_key)}\n"
        f"{key_env_var}={_quote_env_value(ai_api_key)}\n"
        f"MINIZEN_EMAIL_USERNAME={_quote_env_value(email_username)}\n"
        f"MINIZEN_EMAIL_PASSWORD={_quote_env_value(email_password)}\n"
    )
    env_path.chmod(0o600)

    typer.echo(f"\nConfig written to:      {config}")
    typer.echo(f"Credentials written to: {env_path}")


def _quote_env_value(value: str) -> str:
    r"""Wrap a .env value in double quotes, escaping backslashes and double quotes.

    Args:
        value: The raw credential string to quote.

    Returns:
        The value wrapped in double quotes with ``\\`` and ``"`` escaped,
        safe for writing to a ``.env`` file parsed by python-dotenv.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_config(
    *,
    config: Path,
    from_addr: str,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    model: str,
    top_n: int,
    interests: list[str],
    avoid: list[str],
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
        interests: Topics to prioritise; omitted from config when empty.
        avoid: Topics to exclude; omitted from config when empty.
    """
    ai_section: dict[str, object] = {"model": model, "top_n": top_n}
    if interests:
        ai_section["interests"] = interests
    if avoid:
        ai_section["avoid"] = avoid
    data: dict[str, object] = {
        "miniflux": {
            "url": DEFAULT_MINIFLUX_URL,
        },
        "email": {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "from_addr": from_addr,
            "to_addr": to_addr,
        },
        "ai": ai_section,
    }
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(tomli_w.dumps(data).encode())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: all PASS

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "feat: add interests and avoid prompts and CLI flags to setup wizard"
```
