# More LLM Providers — Design Spec

**Date:** 2026-07-28
**Status:** Approved

## Overview

Open minizen to every LLM provider that pydantic-ai supports, instead of the two
(Anthropic, OpenAI) the setup wizard currently allows. DeepSeek is the immediate
motivating provider, but the change is general: any provider following the
`PROVIDER_API_KEY` naming convention works with no minizen code edit, so upgrading
pydantic-ai gains providers for free. Only providers that break the convention need
a one-line table entry.

The AI agent is already provider-agnostic — `DigestAgent.__init__` passes the model
identifier straight to `Agent(model=...)`. The sole blocker is
`_provider_key_info()` in `src/minizen/cli/commands/setup.py`, which hard-codes the
`anthropic:` and `openai:` prefixes and exits with an error for anything else.

### DeepSeek requires no new dependency

Verified against the pinned pydantic-ai 2.12.0:

- `infer_model("deepseek:deepseek-chat")` resolves to an `OpenAIChatModel` whose
  client is `openai.AsyncOpenAI` with `base_url=https://api.deepseek.com`.
- There is no `deepseek` SDK package, and `pydantic-ai-slim` defines no `deepseek`
  extra. DeepSeek's API is OpenAI-wire-compatible, so pydantic-ai reuses the OpenAI
  client.
- `providers/deepseek.py` guards its import with a message naming the `openai`
  optional group.

`pyproject.toml` is therefore unchanged. The dependency stays
`pydantic-ai-slim[anthropic,openai]`.

## Architecture

### New module: `src/minizen/ai/provider_keys.py`

Answers one question: given a model identifier, which API key does the user need?

The name avoids `minizen.ai.providers`, which would collide conceptually with the
existing `minizen.providers` package (RSS and email adapters) despite meaning
something different.

```python
class ProviderKey(NamedTuple):
    prefix: str    # "deepseek"
    label: str     # "DeepSeek API key"  — setup prompt label
    env_var: str   # "DEEPSEEK_API_KEY"
```

`resolve_provider_key(model: str) -> ProviderKey` performs four steps:

1. **Split** on the first `:`. A missing colon raises `ConfigError`.
2. **Validate** the prefix with `pydantic_ai.providers.infer_provider_class`.
   minizen maintains no provider list; pydantic-ai's registry is the source of
   truth.
3. **Derive** the environment variable by convention:
   `prefix.upper().replace("-", "_") + "_API_KEY"`. Checked against every provider
   module in pydantic-ai 2.12.0; holds for anthropic, openai, deepseek, groq,
   mistral, xai, cerebras, fireworks, together, openrouter, moonshotai, nebius,
   sambanova, zai, github, ovhcloud, and alibaba.
4. **Override** the providers that break the convention.

#### Override table

| Prefix | Environment variable |
| --- | --- |
| `cohere` | `CO_API_KEY` |
| `huggingface` | `HF_TOKEN` |
| `heroku` | `HEROKU_INFERENCE_KEY` |
| `vercel` | `VERCEL_AI_GATEWAY_API_KEY` |
| `voyageai` | `VOYAGE_API_KEY` |
| `openai-chat` | `OPENAI_API_KEY` |
| `openai-responses` | `OPENAI_API_KEY` |

Verified against pydantic-ai 2.12.0. Two entries deserve note:

- `google` is **not** in the table: the convention already yields `GOOGLE_API_KEY`,
  which is correct. `google-gla` and `google-vertex` are **not valid prefixes** in
  this version — they were pydantic-ai v0.x names and now raise
  `Unknown provider`. Gemini is reached through `google:`.
- `openai-chat` and `openai-responses` are real prefixes that would derive
  `OPENAI_CHAT_API_KEY` / `OPENAI_RESPONSES_API_KEY` from the convention. Both read
  `OPENAI_API_KEY`.

#### Providers outside the wizard's scope

`bedrock`, `azure`, `azure-responses`, `ollama`, `litellm`, and `google-cloud` need
AWS credentials, an endpoint URL, or a base URL rather than a single API key. The wizard's "one
provider, one secret" shape does not fit them, so `resolve_provider_key` raises
`UnsupportedProviderError` naming the provider and directing the user to configure
the environment manually.

`UnsupportedProviderError` subclasses `ConfigError` but is a **distinct** type,
because these providers are valid — not erroneous. They work at run time when the
user sets up the environment themselves, since `DigestAgent` passes the model
identifier through unchanged. The restriction is on the wizard, not on minizen, and
each caller reacts differently:

| Caller | On `UnsupportedProviderError` | On other `ConfigError` |
| --- | --- | --- |
| `setup` | Exit 1 — the wizard cannot prompt for these credentials | Exit 1 |
| `config validate` | Skip the AI-key check; report that the provider is configured manually | Exit 1 |
| `config set ai.model` | Accept and write the value | Reject, exit 1 |

Collapsing the two into one exception type would make `config validate` reject a
correctly configured Bedrock or Ollama setup, and would block `config set` from ever
writing one.

### `src/minizen/cli/commands/setup.py`

`_provider_key_info()` is deleted. Both call sites — `_setup_non_interactive` and
`_setup_interactive` — call `resolve_provider_key()` instead.

The deleted function called `typer.echo` and raised `typer.Exit` from inside what is
really a lookup, mixing CLI concerns into a mapping. `resolve_provider_key` is pure
and raises `ConfigError`; `setup.py` catches it and performs the echo and exit. This
makes the resolver testable without a CLI runner.

The interactive "AI model" prompt label gains format guidance
(`provider:model`). `DEFAULT_MODEL` remains `anthropic:claude-haiku-4-5` — this
change adds reach without moving the default.

### `src/minizen/cli/commands/config.py`

Two additions that close an existing gap (see Error Handling below):

- **`config validate`** resolves the provider from `ai.model` and confirms its
  environment variable is set, reporting a missing key the same way missing Miniflux
  and email variables are already reported. An `UnsupportedProviderError` is not a
  failure here: the check is skipped and the provider is reported as manually
  configured.
- **`config set ai.model`** validates the identifier through `resolve_provider_key`
  before writing, so a typo cannot land in the config file. An
  `UnsupportedProviderError` still writes, since the identifier is valid. Other keys
  are unaffected.

`src/minizen/config/loader.py` is unchanged. Requiring the AI key inside
`load_settings` would break `config show` for no benefit.

## Error Handling

Add `ConfigError(MinizenError)` and `UnsupportedProviderError(ConfigError)` to
`src/minizen/exceptions.py`.

The current code collapses every failure into `Unknown model provider`. The new
resolver separates four cases:

| Cause | Behaviour |
| --- | --- |
| No `:` in the identifier | `ConfigError`: model must be `provider:model`, e.g. `deepseek:deepseek-chat` |
| `ValueError` from `infer_provider_class` | `ConfigError`: unknown model provider `'<prefix>'` |
| `ImportError` from `infer_provider_class` | `ConfigError` re-raising pydantic-ai's own message |
| Prefix in the out-of-scope set | `UnsupportedProviderError`: configure `<prefix>` manually; the wizard supports single-API-key providers |

The `ImportError` case reuses pydantic-ai's message verbatim rather than
constructing an install hint from the prefix. A provider prefix is not always an
extra name: `cerebras`, `fireworks`, `together`, `moonshotai`, `nebius`,
`sambanova`, `github`, `vercel`, and `alibaba` are OpenAI-compatible and have no
extra of their own, while `groq` and `mistral` do. pydantic-ai's message already
names the correct optional group in each case, so deferring to it is both correct
and self-maintaining.

### Gap being closed

`load_settings` never reads the AI key — pydantic-ai fetches it from the environment
lazily at run time. `minizen config validate` therefore reports "Configuration is
valid" for a config whose AI key is absent, and the failure surfaces at digest time.

With a single supported provider this was a minor risk. With every provider it
becomes a likely one, because the variable name now varies per provider. The
`config validate` check above closes it.

## Dependencies

None. `pyproject.toml` is unchanged.

## Documentation

`README.md`, `docs/configuration.md`, `docs/getting_started.md`, and `docs/faq.md`
state or imply that minizen supports Anthropic or OpenAI. Each is updated to
describe:

- Support for any pydantic-ai provider, via the `provider:model` identifier.
- The `PROVIDER_API_KEY` naming convention and the documented exceptions.
- DeepSeek as a worked example requiring no extra install.
- Installing an extra for providers that need one, using the command pydantic-ai
  reports (for example `uv tool install minizen --with 'pydantic-ai-slim[groq]'`).
- Which providers the wizard cannot configure, and why.

## Testing

Follows the project's conventions: type hints on all parameters including fixtures,
keyword arguments when calling code under test, `assert_called_once_with`,
arrange/act/assert sections, no module-level constants, and `mocker.patch` targeting
the module where a name is used.

### New: `tests/ai/test_provider_keys.py`

- Convention derivation for `anthropic`, `openai`, and `deepseek`.
- Each override-table entry maps to its documented variable.
- Hyphenated prefixes convert to underscores.
- Each out-of-scope provider raises `UnsupportedProviderError`, and that type is
  caught by `except ConfigError` so callers that do not distinguish still work.
- Identifiers without a colon raise `ConfigError`.
- Unknown prefix: `infer_provider_class` patched at
  `minizen.ai.provider_keys.infer_provider_class` to raise `ValueError`.
- Missing SDK: the same name patched to raise `ImportError`, asserting the original
  message is preserved.

Resolution performs no network access, so happy paths run against the real
pydantic-ai registry.

### Updated: `tests/cli/commands/test_setup.py`

Lines 322 and 386 assert on the string `"Unknown model provider"`. The new error
message deliberately preserves that wording (`Unknown model provider: 'unknown'.`),
so both tests keep passing unchanged — the phrasing is a compatibility constraint,
not an accident.

A DeepSeek case is added, asserting `DEEPSEEK_API_KEY` is written to the generated
`.env`.

### Updated: config command tests

Cover `config validate` reporting a missing AI key, and `config set ai.model`
rejecting an invalid identifier while accepting a valid one. Both commands are also
tested against an out-of-scope provider: `validate` must pass without demanding a
key, and `set` must write the value.
