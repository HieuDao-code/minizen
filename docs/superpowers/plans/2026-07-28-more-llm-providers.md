# More LLM Providers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let minizen use any LLM provider pydantic-ai supports, instead of only Anthropic and OpenAI, with DeepSeek working out of the box.

**Architecture:** A new pure module `src/minizen/ai/provider_keys.py` maps a `provider:model` identifier to the API key the user must supply. It validates the prefix through pydantic-ai's own `infer_provider_class` registry rather than a list minizen maintains, derives the environment variable from the `PROVIDER_API_KEY` convention, and consults a small override table for the providers that break it. The CLI (`setup`, `config validate`, `config set`) consumes this resolver and translates its exceptions into user-facing messages.

**Tech Stack:** Python 3.14, pydantic-ai 2.12.0 (`pydantic-ai-slim[anthropic,openai]`), typer, pytest + pytest-mock, ruff, ty, uv.

## Global Constraints

- **Package manager is `uv`.** Never invoke `pip`. Run tests as `uv run pytest ...`.
- **Test coverage gate is 100%** (`--cov-fail-under=100` in `pyproject.toml`). Running a subset of tests will fail this gate, so **every single-test command in this plan passes `--no-cov`**. The full suite runs without that flag at the end of each task.
- **Ruff runs with `select = ["ALL"]`**, ignoring only `B904` and `COM812`. Consequences you must respect:
  - Never pass a string literal directly to an exception. Assign to a local `msg` first, then `raise SomeError(msg)` (rules `EM101`/`EM102`/`TRY003`). This is the existing pattern in `src/minizen/ai/agent.py:220-221`.
  - Never use a bare `except: pass` (rule `S110`); use an explicit `return`.
  - Line length is ruff's default 88; add `# noqa: E501` only where the codebase already does.
- **Docstrings are required** on every module, class, function, and method, in Google style with `Args:`, `Returns:`, and `Raises:` sections. Omit sections that do not apply (no `Returns:` for `-> None`). Tests are exempt (`per-file-ignores` disables `D` under `**/tests/**`).
- **Test conventions** (from `CLAUDE.md`):
  - Type hints on every test parameter, fixtures included.
  - Keyword arguments when calling the code under test.
  - `assert_called_once_with(...)` rather than `assert_called_once()` plus separate argument checks.
  - `# arrange` / `# act` / `# assert` comment sections separated by blank lines, without verbose narration.
  - No module-level constants in test files. A `@pytest.mark.parametrize` inline list is not a module-level constant and is fine.
  - `mocker.patch` targets the **module where the name is used**, e.g. `minizen.ai.provider_keys.infer_provider_class`.
- **`pyproject.toml` does not change.** DeepSeek rides the already-installed `openai` client; `pydantic-ai-slim` defines no `deepseek` extra.
- **`DEFAULT_MODEL` stays `anthropic:claude-haiku-4-5`.**
- **Verified provider facts** (pydantic-ai 2.12.0) — do not re-derive:
  - Valid prefixes include `anthropic`, `openai`, `openai-chat`, `openai-responses`, `deepseek`, `google`, `google-cloud`, `azure`, `azure-responses`, `groq`, `mistral`, `cohere`, `xai`, `huggingface`, `heroku`, `vercel`, `voyageai`, `bedrock`, `ollama`, `litellm`, `github`.
  - `google-gla` and `google-vertex` are **invalid** (pydantic-ai v0.x names). Gemini is reached via `google:`.
  - `infer_provider_class` raises `ValueError` for an unknown prefix and `ImportError` (naming the correct extra) when the provider's SDK is absent.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `src/minizen/exceptions.py` | Modify: add `ConfigError` and `UnsupportedProviderError`. |
| `src/minizen/ai/provider_keys.py` | Create: the pure resolver. No typer import, no I/O. |
| `src/minizen/__init__.py` | Modify: export the two new exceptions. |
| `src/minizen/cli/commands/setup.py` | Modify: delete `_provider_key_info`, consume the resolver, translate errors to CLI output. |
| `src/minizen/cli/commands/config.py` | Modify: `validate` checks the AI key; `set` validates `ai.model`. |
| `tests/ai/test_provider_keys.py` | Create: resolver unit tests. |
| `tests/test_exceptions.py` | Modify: hierarchy assertions for the new exceptions. |
| `tests/test_public_api.py` | Modify: the exported-symbol set. |
| `tests/cli/commands/test_setup.py` | Modify: add a DeepSeek path. |
| `tests/cli/commands/test_config.py` | Modify: AI-key validate and `set ai.model` cases. |
| `README.md`, `docs/configuration.md`, `docs/getting_started.md`, `docs/faq.md` | Modify: provider documentation. |

The resolver stays free of typer so it is testable without a `CliRunner`. The current `_provider_key_info` mixes `typer.echo`/`typer.Exit` into what is really a lookup; that separation is the point of the split.

---

## Task 1: Exceptions and the provider-key resolver

**Files:**
- Modify: `src/minizen/exceptions.py`
- Create: `src/minizen/ai/provider_keys.py`
- Modify: `src/minizen/__init__.py:14` (import line) and `:18-33` (`__all__`)
- Test: `tests/ai/test_provider_keys.py` (create), `tests/test_exceptions.py`, `tests/test_public_api.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `minizen.exceptions.ConfigError(MinizenError)`
  - `minizen.exceptions.UnsupportedProviderError(ConfigError)`
  - `minizen.ai.provider_keys.ProviderKey` — `NamedTuple` with fields `prefix: str`, `label: str`, `env_var: str`
  - `minizen.ai.provider_keys.resolve_provider_key(*, model: str) -> ProviderKey` — keyword-only, raises `ConfigError` or `UnsupportedProviderError`

- [ ] **Step 1: Write the failing exception-hierarchy tests**

Append to `tests/test_exceptions.py`, and update its existing import line to
`from minizen.exceptions import (AIError, ConfigError, EmailError, MinifluxError, MinizenError, UnsupportedProviderError)`:

```python
def test_config_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(ConfigError, MinizenError)


def test_unsupported_provider_error_is_config_error() -> None:
    # act / assert
    assert issubclass(UnsupportedProviderError, ConfigError)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_exceptions.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'ConfigError'`

- [ ] **Step 3: Add the exceptions**

Append to `src/minizen/exceptions.py`:

```python
class ConfigError(MinizenError):
    """Raised when the configuration is invalid or incomplete."""


class UnsupportedProviderError(ConfigError):
    """Raised for a valid provider the setup wizard cannot configure.

    These providers (for example ``bedrock`` and ``ollama``) need AWS
    credentials or a base URL rather than a single API key. They still work at
    run time when the user configures the environment themselves, so callers
    should treat this as informational rather than as a failure.
    """
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_exceptions.py -v --no-cov`
Expected: PASS (6 tests)

- [ ] **Step 5: Write the failing resolver tests**

Create `tests/ai/test_provider_keys.py`:

```python
from typing import TYPE_CHECKING

import pytest

from minizen.ai.provider_keys import resolve_provider_key
from minizen.exceptions import ConfigError, UnsupportedProviderError

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_resolves_anthropic_by_convention() -> None:
    # act
    result = resolve_provider_key(model="anthropic:claude-haiku-4-5")

    # assert
    assert result.prefix == "anthropic"
    assert result.env_var == "ANTHROPIC_API_KEY"
    assert result.label == "Anthropic API key"


def test_resolves_deepseek_without_extra_dependency() -> None:
    # act
    result = resolve_provider_key(model="deepseek:deepseek-chat")

    # assert
    assert result.prefix == "deepseek"
    assert result.env_var == "DEEPSEEK_API_KEY"
    assert result.label == "DeepSeek API key"


def test_resolves_openai_with_display_name_override() -> None:
    # act
    result = resolve_provider_key(model="openai:gpt-4o")

    # assert
    assert result.env_var == "OPENAI_API_KEY"
    assert result.label == "OpenAI API key"


def test_model_name_may_contain_colons() -> None:
    # act
    result = resolve_provider_key(model="openai:ft:gpt-4o:custom")

    # assert
    assert result.prefix == "openai"
    assert result.env_var == "OPENAI_API_KEY"


@pytest.mark.parametrize(
    ("model", "expected_env_var"),
    [
        ("cohere:command-r", "CO_API_KEY"),
        ("huggingface:meta-llama/Llama-3-8B", "HF_TOKEN"),
        ("heroku:claude-3-5-sonnet", "HEROKU_INFERENCE_KEY"),
        ("vercel:anthropic/claude-sonnet-4", "VERCEL_AI_GATEWAY_API_KEY"),
        ("voyageai:voyage-3", "VOYAGE_API_KEY"),
        ("openai-chat:gpt-4o", "OPENAI_API_KEY"),
        ("openai-responses:gpt-4o", "OPENAI_API_KEY"),
    ],
)
def test_override_table_wins_over_convention(
    model: str, expected_env_var: str, mocker: MockerFixture
) -> None:
    # arrange
    mocker.patch("minizen.ai.provider_keys.infer_provider_class")

    # act
    result = resolve_provider_key(model=model)

    # assert
    assert result.env_var == expected_env_var


@pytest.mark.parametrize(
    "model",
    [
        "bedrock:anthropic.claude-3-5-sonnet-20240620-v1:0",
        "azure:gpt-4o",
        "azure-responses:gpt-4o",
        "ollama:llama3",
        "litellm:gpt-4o",
        "google-cloud:gemini-2.0-flash",
    ],
)
def test_unsupported_providers_raise_unsupported_provider_error(model: str) -> None:
    # act / assert
    with pytest.raises(UnsupportedProviderError, match="cannot configure"):
        resolve_provider_key(model=model)


def test_unsupported_provider_error_is_catchable_as_config_error() -> None:
    # act / assert
    with pytest.raises(ConfigError):
        resolve_provider_key(model="ollama:llama3")


def test_identifier_without_colon_is_rejected() -> None:
    # act / assert
    with pytest.raises(ConfigError, match="Expected 'provider:model'"):
        resolve_provider_key(model="claude-haiku-4-5")


def test_unknown_prefix_is_rejected() -> None:
    # act / assert
    with pytest.raises(ConfigError, match="Unknown model provider"):
        resolve_provider_key(model="notaprovider:some-model")


def test_missing_sdk_reports_pydantic_ai_install_hint(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch(
        "minizen.ai.provider_keys.infer_provider_class",
        side_effect=ImportError("install the `groq` package — pydantic-ai-slim[groq]"),
    )

    # act / assert
    with pytest.raises(ConfigError, match=r"pydantic-ai-slim\[groq\]"):
        resolve_provider_key(model="groq:llama-3.3-70b")
```

**Do not remove the `mocker.patch` in `test_override_table_wins_over_convention`.**
The `cohere`, `huggingface` and `voyageai` SDKs are not installed, so without the
patch `infer_provider_class` raises `ImportError` and the resolver returns the
install hint before ever consulting the override table. That is correct product
behaviour — a user selecting `cohere:` without the SDK *should* get the install
hint — so the test is what must adapt. Stubbing the registry also keeps the test
about the mapping, and keeps it passing on a machine where someone has installed
those extras. The unmocked tests use only `anthropic`, `openai` and `deepseek`,
whose clients ship by default.

- [ ] **Step 6: Run to verify it fails**

Run: `uv run pytest tests/ai/test_provider_keys.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'minizen.ai.provider_keys'`

- [ ] **Step 7: Implement the resolver**

Create `src/minizen/ai/provider_keys.py`:

```python
"""Map a pydantic-ai model identifier to the API key its provider requires."""

from typing import NamedTuple

from pydantic_ai.providers import infer_provider_class

from minizen.exceptions import ConfigError, UnsupportedProviderError

_KEY_ENV_OVERRIDES: dict[str, str] = {
    "cohere": "CO_API_KEY",
    "heroku": "HEROKU_INFERENCE_KEY",
    "huggingface": "HF_TOKEN",
    "openai-chat": "OPENAI_API_KEY",
    "openai-responses": "OPENAI_API_KEY",
    "vercel": "VERCEL_AI_GATEWAY_API_KEY",
    "voyageai": "VOYAGE_API_KEY",
}

_DISPLAY_NAMES: dict[str, str] = {
    "deepseek": "DeepSeek",
    "github": "GitHub",
    "huggingface": "Hugging Face",
    "moonshotai": "Moonshot AI",
    "openai": "OpenAI",
    "openai-chat": "OpenAI",
    "openai-responses": "OpenAI",
    "openrouter": "OpenRouter",
    "ovhcloud": "OVHcloud",
    "sambanova": "SambaNova",
    "voyageai": "Voyage AI",
    "xai": "xAI",
    "zai": "Z.ai",
}

_UNSUPPORTED_PREFIXES: frozenset[str] = frozenset({
    "azure",
    "azure-responses",
    "bedrock",
    "google-cloud",
    "litellm",
    "ollama",
})


class ProviderKey(NamedTuple):
    """The API key requirement for a model identifier's provider."""

    prefix: str
    label: str
    env_var: str


def resolve_provider_key(*, model: str) -> ProviderKey:
    """Resolve which API key the provider in *model* requires.

    Validates the provider prefix against pydantic-ai's own registry, so
    minizen never maintains a provider list of its own.

    Args:
        model: pydantic-ai model identifier, e.g. ``deepseek:deepseek-chat``.

    Returns:
        A ``ProviderKey`` naming the provider, its prompt label, and the
        environment variable holding its API key.

    Raises:
        UnsupportedProviderError: If the provider is valid but needs more than
            a single API key, so the setup wizard cannot configure it.
        ConfigError: If *model* has no ``provider:`` prefix, the prefix is not a
            known provider, or the provider's SDK is not installed.
    """
    if ":" not in model:
        msg = (
            f"Invalid model identifier: {model!r}. "
            "Expected 'provider:model', for example 'deepseek:deepseek-chat'."
        )
        raise ConfigError(msg)

    prefix = model.split(":", maxsplit=1)[0]

    if prefix in _UNSUPPORTED_PREFIXES:
        msg = (
            f"The setup wizard cannot configure the {prefix!r} provider, which "
            "needs more than a single API key. Set its environment variables "
            "yourself and edit ai.model directly."
        )
        raise UnsupportedProviderError(msg)

    try:
        infer_provider_class(prefix)
    except ValueError as exc:
        msg = f"Unknown model provider: {prefix!r}."
        raise ConfigError(msg) from exc
    except ImportError as exc:
        msg = f"Provider {prefix!r} needs an extra package. {exc}"
        raise ConfigError(msg) from exc

    env_var = _KEY_ENV_OVERRIDES.get(
        prefix, f"{prefix.upper().replace('-', '_')}_API_KEY"
    )
    display = _DISPLAY_NAMES.get(prefix, prefix.replace("-", " ").title())
    return ProviderKey(prefix=prefix, label=f"{display} API key", env_var=env_var)
```

The `Unknown model provider` wording is a **compatibility constraint**: two existing tests in `tests/cli/commands/test_setup.py` (lines 322 and 386) assert on that substring. Keeping it means those tests need no change.

- [ ] **Step 8: Run to verify it passes**

Run: `uv run pytest tests/ai/test_provider_keys.py -v --no-cov`
Expected: PASS (all tests, including the 7 parametrized override cases and 6 parametrized unsupported cases)

- [ ] **Step 9: Export the new exceptions**

In `src/minizen/__init__.py`, change the exceptions import to:

```python
from minizen.exceptions import (
    AIError,
    ConfigError,
    EmailError,
    MinifluxError,
    MinizenError,
    UnsupportedProviderError,
)
```

and add `"ConfigError",` and `"UnsupportedProviderError",` to `__all__`, keeping it alphabetically sorted (ruff `RUF022` enforces this). `"ConfigError"` goes after `"Article"`; `"UnsupportedProviderError"` goes after `"Settings"`.

- [ ] **Step 10: Update the public-API test**

In `tests/test_public_api.py`: add `ConfigError` and `UnsupportedProviderError` to the `from minizen import (...)` block and to the `from minizen.exceptions import (...)` aliased block (as `_ConfigError`, `_UnsupportedProviderError`), add both names to the `expected` set in `test_top_level_all`, and append to `test_exception_imports_are_same_objects`:

```python
    assert ConfigError is _ConfigError
    assert UnsupportedProviderError is _UnsupportedProviderError
```

- [ ] **Step 11: Run the full suite**

Run: `uv run pytest`
Expected: PASS with 100% coverage. If coverage is below 100%, the report's `term-missing` column names the uncovered line — add a test for it rather than lowering the gate.

- [ ] **Step 12: Lint and type-check**

Run: `uv run ruff check && uv run ruff format --check && uv run ty check`
Expected: clean. If `ruff format --check` fails, run `uv run ruff format` and re-run.

- [ ] **Step 13: Commit**

```bash
git add src/minizen/exceptions.py src/minizen/ai/provider_keys.py src/minizen/__init__.py tests/ai/test_provider_keys.py tests/test_exceptions.py tests/test_public_api.py
git commit -m "feat(ai): resolve provider API keys from the pydantic-ai registry"
```

---

## Task 2: Rewire the setup wizard

**Files:**
- Modify: `src/minizen/cli/commands/setup.py:20-38` (delete `_provider_key_info`), `:158`, `:236`, `:212`
- Test: `tests/cli/commands/test_setup.py`

**Interfaces:**
- Consumes: `resolve_provider_key(*, model: str) -> ProviderKey` and `ConfigError` from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing DeepSeek tests**

Append to `tests/cli/commands/test_setup.py`:

```python
def test_setup_interactive_writes_deepseek_key_to_env(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "deepseek:deepseek-chat\n"
            "\n"  # top_n
            "\n"  # interests
            "\n"  # avoid
            "\n"  # smtp host
            "\n"  # smtp port
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "deepseek-api-key\n"
        ),
    )

    # assert
    assert result.exit_code == 0
    assert "DeepSeek API key" in result.output
    env_text = (config_path.parent / ".env").read_text()
    assert 'DEEPSEEK_API_KEY="deepseek-api-key"' in env_text


def test_setup_non_interactive_accepts_deepseek_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-key")
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
            "--model",
            "deepseek:deepseek-chat",
        ],
    )

    # assert
    assert result.exit_code == 0
    assert tomllib.loads(config_path.read_text())["ai"]["model"] == (
        "deepseek:deepseek-chat"
    )


def test_setup_rejects_provider_needing_more_than_a_key(
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
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
            "--model",
            "ollama:llama3",
        ],
    )

    # assert
    assert result.exit_code != 0
    assert "cannot configure" in result.output
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/cli/commands/test_setup.py -v --no-cov`
Expected: FAIL — the DeepSeek cases exit non-zero with `Unknown model provider: deepseek`, because `_provider_key_info` still hard-codes two prefixes.

- [ ] **Step 3: Replace `_provider_key_info`**

In `src/minizen/cli/commands/setup.py`, delete the whole `_provider_key_info` function (lines 20-38) and add these imports below the existing ones:

```python
from minizen.ai.provider_keys import ProviderKey, resolve_provider_key
from minizen.exceptions import ConfigError
```

Add this replacement function in its place:

```python
def _provider_key(model: str) -> ProviderKey:
    """Resolve the provider API key for *model*, exiting on any failure.

    Args:
        model: pydantic-ai model identifier (e.g. ``deepseek:deepseek-chat``).

    Returns:
        The ``ProviderKey`` describing the required API key.

    Raises:
        typer.Exit: If the identifier is invalid, names an unknown provider,
            needs an uninstalled package, or cannot be configured by the wizard.
    """
    try:
        return resolve_provider_key(model=model)
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc
```

`UnsupportedProviderError` subclasses `ConfigError`, so this one handler covers it — the wizard genuinely cannot proceed for those providers.

- [ ] **Step 4: Update the two call sites**

At `src/minizen/cli/commands/setup.py:158`, replace:

```python
    _, ai_key_var = _provider_key_info(model)
```

with:

```python
    ai_key_var = _provider_key(model).env_var
```

At `:236`, replace:

```python
    key_label, key_env_var = _provider_key_info(resolved_model)
    ai_api_key = typer.prompt(key_label, hide_input=True)
```

with:

```python
    provider = _provider_key(resolved_model)
    ai_api_key = typer.prompt(provider.label, hide_input=True)
```

Then at `:256`, change `f"{key_env_var}={_quote_env_value(ai_api_key)}\n"` to
`f"{provider.env_var}={_quote_env_value(ai_api_key)}\n"`.

- [ ] **Step 5: Update the model prompt label**

At `src/minizen/cli/commands/setup.py:212`, change:

```python
    resolved_model = typer.prompt("AI model", default=model or DEFAULT_MODEL)
```

to:

```python
    resolved_model = typer.prompt(
        "AI model (provider:model)", default=model or DEFAULT_MODEL
    )
```

- [ ] **Step 6: Run the setup tests**

Run: `uv run pytest tests/cli/commands/test_setup.py -v --no-cov`
Expected: PASS, including the two pre-existing `"Unknown model provider"` assertions at lines 322 and 386, which the preserved wording keeps green.

- [ ] **Step 7: Run the full suite, lint, and type-check**

Run: `uv run pytest && uv run ruff check && uv run ruff format --check && uv run ty check`
Expected: PASS with 100% coverage, clean lint and types.

- [ ] **Step 8: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "feat(setup): accept any pydantic-ai provider in the wizard"
```

---

## Task 3: Validate the AI key in the config commands

**Files:**
- Modify: `src/minizen/cli/commands/config.py:47-59` (`validate`), `:73-106` (`set_value`)
- Test: `tests/cli/commands/test_config.py`

**Interfaces:**
- Consumes: `resolve_provider_key`, `ConfigError`, `UnsupportedProviderError` from Task 1.
- Produces: nothing later tasks depend on.

**Why:** `load_settings` never reads the AI key — pydantic-ai fetches it lazily at run time — so `config validate` currently reports success for a config whose AI key is missing entirely, and the failure surfaces at digest time. With one provider that was a minor risk; with every provider the variable name varies per provider, making it likely.

- [ ] **Step 1: Write the failing config tests**

Append to `tests/cli/commands/test_config.py`. Note `_minimal_config` writes no `ai` section, so `ai.model` falls back to `DEFAULT_MODEL` (`anthropic:claude-haiku-4-5`):

```python
def test_config_validate_fails_when_ai_key_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])

    # assert
    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output


def test_config_validate_skips_key_check_for_manual_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _write_config(
        config_path,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
            "ai": {"model": "ollama:llama3"},
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    assert "configured manually" in result.output


def test_config_validate_fails_on_unknown_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _write_config(
        config_path,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
            "ai": {"model": "notaprovider:some-model"},
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])

    # assert
    assert result.exit_code == 1
    assert "Unknown model provider" in result.output


def test_config_set_rejects_invalid_model(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["config", "set", "ai.model", "notaprovider:x", "--config", str(config_path)],
    )

    # assert
    assert result.exit_code == 1
    assert "Unknown model provider" in result.output


def test_config_set_accepts_deepseek_model(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "ai.model",
            "deepseek:deepseek-chat",
            "--config",
            str(config_path),
        ],
    )

    # assert
    assert result.exit_code == 0
    assert tomllib.loads(config_path.read_text())["ai"]["model"] == (
        "deepseek:deepseek-chat"
    )


def test_config_set_accepts_manual_provider_model(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["config", "set", "ai.model", "ollama:llama3", "--config", str(config_path)],
    )

    # assert
    assert result.exit_code == 0
    assert tomllib.loads(config_path.read_text())["ai"]["model"] == "ollama:llama3"
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/cli/commands/test_config.py -v --no-cov`
Expected: FAIL — validate reports "Configuration is valid." with no AI key, and `set` writes an invalid model without complaint.

- [ ] **Step 3: Add the imports and a shared model validator**

In `src/minizen/cli/commands/config.py`, add `import os` to the stdlib imports and these below the existing minizen imports:

```python
from minizen.ai.provider_keys import resolve_provider_key
from minizen.exceptions import ConfigError, UnsupportedProviderError
```

Add this helper after the `app = typer.Typer(...)` line:

```python
def _check_model(model: str) -> None:
    """Exit with an error when *model* is not a usable model identifier.

    A provider the wizard cannot configure is accepted: the identifier is
    valid and works once the user sets up its environment.

    Args:
        model: pydantic-ai model identifier from the config file.

    Raises:
        typer.Exit: If the identifier is malformed, names an unknown provider,
            or needs an uninstalled package.
    """
    try:
        resolve_provider_key(model=model)
    except UnsupportedProviderError:
        return
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc
```

The explicit `return` rather than `pass` avoids ruff `S110`.

- [ ] **Step 4: Add the AI-key check to `validate`**

Replace the body of `validate` (`src/minizen/cli/commands/config.py:49-59`) with:

```python
    """Validate the configuration file and environment variables."""
    try:
        settings = load_settings(config_path=config)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)

    try:
        provider = resolve_provider_key(model=settings.ai.model)
    except UnsupportedProviderError:
        typer.echo(f"AI provider configured manually: {settings.ai.model}")
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc
    else:
        if not os.environ.get(provider.env_var):
            typer.echo(f"Error: missing environment variable {provider.env_var}")
            raise typer.Exit(code=1)

    typer.echo("Configuration is valid.")
```

The only change to the first block is capturing the return value as `settings`.

- [ ] **Step 5: Validate `ai.model` in `set`**

In `set_value`, immediately after the `_ALLOWED_KEYS` membership check and before the config file is opened, insert:

```python
    if key == "ai.model":
        _check_model(value)
```

- [ ] **Step 6: Run the config tests**

Run: `uv run pytest tests/cli/commands/test_config.py -v --no-cov`
Expected: PASS

- [ ] **Step 7: Run the full suite, lint, and type-check**

Run: `uv run pytest && uv run ruff check && uv run ruff format --check && uv run ty check`
Expected: PASS with 100% coverage, clean lint and types.

Existing tests set no AI key, so some may now fail validate. If `test_config_validate_succeeds_with_valid_config` fails, add `monkeypatch.setenv("ANTHROPIC_API_KEY", "ai-key")` to its arrange block — that reflects the intended new behaviour, not a regression.

- [ ] **Step 8: Commit**

```bash
git add src/minizen/cli/commands/config.py tests/cli/commands/test_config.py
git commit -m "feat(config): verify the AI provider key during validate"
```

---

## Task 4: Documentation

**Files:**
- Modify: `README.md`, `docs/configuration.md`, `docs/getting_started.md`, `docs/faq.md`

**Interfaces:**
- Consumes: the behaviour built in Tasks 1-3.
- Produces: nothing.

**Context:** `docs/configuration.md:89-90` and `docs/faq.md:10-11` already claim *"any provider it supports will work"*. That claim was **false** — the setup wizard rejected every prefix but two. These edits make the documentation true and fill in what the reader actually needs to act on it.

- [ ] **Step 1: Update the `README.md` feature bullet**

`README.md:22-23` currently reads:

```markdown
- **Pluggable AI** — works with Anthropic Claude or OpenAI models via
  [pydantic-ai](https://ai.pydantic.dev/)
```

Replace with:

```markdown
- **Pluggable AI** — works with any [pydantic-ai](https://ai.pydantic.dev/) provider:
  Anthropic, OpenAI, DeepSeek, Google, Groq, Mistral and more
```

- [ ] **Step 2: Expand the supported-models table in `docs/configuration.md`**

Replace the table at `docs/configuration.md:92-95`:

```markdown
| Provider  | Example `model` value        | Required env var    |
| --------- | ---------------------------- | ------------------- |
| Anthropic | `anthropic:claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| OpenAI    | `openai:gpt-4o-mini`         | `OPENAI_API_KEY`    |
```

with:

```markdown
| Provider  | Example `model` value        | Required env var    | Extra install needed |
| --------- | ---------------------------- | ------------------- | -------------------- |
| Anthropic | `anthropic:claude-haiku-4-5` | `ANTHROPIC_API_KEY` | no                   |
| OpenAI    | `openai:gpt-4o-mini`         | `OPENAI_API_KEY`    | no                   |
| DeepSeek  | `deepseek:deepseek-chat`     | `DEEPSEEK_API_KEY`  | no                   |
| Google    | `google:gemini-2.0-flash`    | `GOOGLE_API_KEY`    | yes                  |
| Groq      | `groq:llama-3.3-70b`         | `GROQ_API_KEY`      | yes                  |
| Mistral   | `mistral:mistral-large`      | `MISTRAL_API_KEY`   | yes                  |

DeepSeek needs no extra install because its API is OpenAI-compatible and reuses the
OpenAI client minizen already ships.

##### Naming the API key

For nearly every provider the environment variable is the provider name uppercased
plus `_API_KEY` — `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`. These are
the exceptions:

| Provider prefix    | Environment variable        |
| ------------------ | --------------------------- |
| `cohere`           | `CO_API_KEY`                |
| `huggingface`      | `HF_TOKEN`                  |
| `heroku`           | `HEROKU_INFERENCE_KEY`      |
| `vercel`           | `VERCEL_AI_GATEWAY_API_KEY` |
| `voyageai`         | `VOYAGE_API_KEY`            |
| `openai-chat`      | `OPENAI_API_KEY`            |
| `openai-responses` | `OPENAI_API_KEY`            |

`minizen setup` prompts for the right variable automatically, and
`minizen config validate` checks that it is set.

##### Providers needing an extra package

When a provider's SDK is missing, `minizen setup` reports the exact command, for
example:

```bash
uv tool install minizen --with 'pydantic-ai-slim[groq]'
```

##### Providers the wizard cannot configure

`bedrock`, `azure`, `azure-responses`, `ollama`, `litellm` and `google-cloud` need
AWS credentials, an endpoint or a base URL rather than a single API key, so
`minizen setup` cannot prompt for them. They still work: set their environment
variables yourself, then point minizen at the model.

```bash
minizen config set ai.model "ollama:llama3"
```

`minizen config validate` reports these as configured manually and skips the key
check.
```

- [ ] **Step 3: Update the env-var table in `docs/configuration.md`**

At `docs/configuration.md:122-123`, replace these two rows:

```markdown
| `ANTHROPIC_API_KEY`      | Anthropic API key (if using an Anthropic model) |
| `OPENAI_API_KEY`         | OpenAI API key (if using an OpenAI model)       |
```

with:

```markdown
| `<PROVIDER>_API_KEY`     | API key for the provider named in `ai.model`, e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` (see [Naming the API key](#naming-the-api-key)) |
```

- [ ] **Step 4: Update the `docs/getting_started.md` prompt table**

At `docs/getting_started.md:41`, replace the **AI model** row's description with:

```markdown
| **AI model**               | Model identifier as `provider:model`, e.g. `anthropic:claude-haiku-4-5`, `openai:gpt-4o` or `deepseek:deepseek-chat` |
```

At `docs/getting_started.md:50`, replace the **AI provider API key** row with:

```markdown
| **AI provider API key**    | The wizard prompts for whichever provider your model names, and writes the matching variable — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, and so on |
```

- [ ] **Step 5: Update `docs/faq.md`**

Replace the two bullets at `docs/faq.md:13-14`:

```markdown
- **Anthropic** — set `model = "anthropic:claude-haiku-4-5"` and provide `ANTHROPIC_API_KEY`
- **OpenAI** — set `model = "openai:gpt-4o-mini"` and provide `OPENAI_API_KEY`
```

with:

```markdown
Working with a default install, no extra package needed:

- **Anthropic** — set `model = "anthropic:claude-haiku-4-5"` and provide `ANTHROPIC_API_KEY`
- **OpenAI** — set `model = "openai:gpt-4o-mini"` and provide `OPENAI_API_KEY`
- **DeepSeek** — set `model = "deepseek:deepseek-chat"` and provide `DEEPSEEK_API_KEY`

Others — Google, Groq, Mistral, xAI, Cohere and the rest — work once their SDK is
installed. `minizen setup` tells you the exact command if it is missing.
```

- [ ] **Step 6: Update the two secret-file examples in `docs/configuration.md`**

At `docs/configuration.md:180`, change:

```dotenv
ANTHROPIC_API_KEY=your-anthropic-key   # or OPENAI_API_KEY
```

to:

```dotenv
ANTHROPIC_API_KEY=your-anthropic-key   # match the provider in ai.model
```

At `docs/configuration.md:198`, change:

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"   # or OPENAI_API_KEY
```

to:

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"   # match the provider in ai.model
```

- [ ] **Step 7: Verify no stale claims remain**

Run: `grep -rn "Anthropic Claude or OpenAI\|Anthropic or OpenAI\|or OPENAI_API_KEY" README.md docs/*.md`
Expected: no output.

- [ ] **Step 8: Build the docs**

Run: `uv run zensical build`
Expected: builds cleanly, with no warnings about the edited files. (`build`, `serve` and `new` are zensical's three subcommands; `just docs` runs `zensical serve --open` if you want to inspect the rendered pages.)

- [ ] **Step 9: Commit**

```bash
git add README.md docs/configuration.md docs/getting_started.md docs/faq.md
git commit -m "docs: document support for all pydantic-ai providers"
```

---

## Final Verification

- [ ] **Run the complete gate**

Run: `just test`
Expected: every tox environment passes — `py314` (pytest at 100% coverage), `lint`, `typing`, `security`. The `commit-msg` environment checks commit messages against commitizen over `origin/main..HEAD`; the messages in this plan follow the required `type(scope): subject` form.

- [ ] **Manual smoke check**

```bash
uv run minizen setup --no-interactive --config /tmp/mz-check.toml \
  --from-addr a@example.com --to-addr b@example.com --model deepseek:deepseek-chat
```

With `MINIFLUX_API_KEY`, `DEEPSEEK_API_KEY`, `MINIZEN_EMAIL_USERNAME`, and `MINIZEN_EMAIL_PASSWORD` exported, this exits 0. Unset `DEEPSEEK_API_KEY` and it must fail naming that variable. Remove `/tmp/mz-check.toml` afterwards.
