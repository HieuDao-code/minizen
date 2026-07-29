# Bundle Google Gemini — Design Spec

**Date:** 2026-07-29
**Status:** Approved

## Overview

Promote Google Gemini from a provider that works *after* the user installs an extra
package to one that works on a plain `uv tool install minizen`, joining Anthropic,
OpenAI and DeepSeek in the zero-install tier.

This is a packaging change, not a feature. The provider plumbing added by
[More LLM Providers](2026-07-28-more-llm-providers-design.md) already handles Gemini
correctly; the only thing standing between a fresh install and a working
`google:gemini-2.0-flash` is the missing `google-genai` SDK.

## Current behaviour

Verified against the pinned pydantic-ai 2.12.0:

- `infer_provider_class("google")` resolves to `GoogleProvider`, so `google` is a
  valid prefix. It is absent from `_UNSUPPORTED_PREFIXES`, so the setup wizard is
  willing to configure it.
- `resolve_provider_key(model="google:gemini-2.0-flash")` needs no table entry. The
  naming convention yields `GOOGLE_API_KEY`, and `"google".title()` yields the
  display name `Google`.
- `GoogleProvider.__init__` reads `GOOGLE_API_KEY`, falling back to `GEMINI_API_KEY`
  for backwards compatibility. The convention-derived variable is therefore the
  correct one.
- `pyproject.toml` requires `pydantic-ai-slim[anthropic,openai]`, so `google-genai`
  is absent and `resolve_provider_key` raises `ConfigError` naming the missing
  package.

Only the last point changes.

## Dependency change

`pyproject.toml`:

```toml
"pydantic-ai-slim[anthropic,google,openai]>=2.12.0,<3.0.0",
```

`uv.lock` is refreshed to match.

Resolved against the lock, this adds nine packages: `google-genai`, `google-auth`,
`websockets`, `cryptography`, `cffi`, `pycparser`, `pyasn1`, `pyasn1-modules` and
their build glue. The `cryptography`/`cffi`/`pyasn1` group arrives through
`google-auth`, not `google-genai` directly. Requirements already in the tree —
`anyio`, `httpx`, `pydantic`, `tenacity`, `typing-extensions`, `sniffio`,
`requests` — are unaffected. The heavyweight optional dependencies (`torch`,
`torchvision`, `transformers`, `sentencepiece`, `pillow`) sit behind
`google-genai`'s `local-tokenizer` extra and are not installed.

`google-genai` emits a `DeprecationWarning` about `_UnionGenericAlias` on Python
3.14. It is benign and the suite does not run warnings-as-errors, but it will
surface in pytest output until google-genai fixes it.

One constraint interaction is worth recording: `google-genai` requires
`tenacity<9.2.0`, while minizen allows `tenacity<10.0.0`. The effective ceiling for
minizen installs drops to 9.2.0. This resolves today and is compatible with
minizen's `tenacity>=9.1.4` floor, but a future tenacity upgrade will need
`google-genai` to move first.

## Source changes

None. `src/minizen/ai/provider_keys.py` needs no new entry in `_KEY_ENV_OVERRIDES`
(the convention is already right) and none in `_DISPLAY_NAMES` (`.title()` is
already right).

`google-cloud` stays in `_UNSUPPORTED_PREFIXES`. Vertex AI needs a project and
location rather than a single API key, so the wizard still cannot configure it —
bundling the SDK does not change that, and the existing test covering the
`google-cloud:` rejection continues to apply.

## Documentation changes

- `docs/configuration.md` — in the supported-models table, Google's "Extra install
  needed" column flips from `yes` to `no`. The sentence below the table explaining
  why DeepSeek needs no extra install is extended to cover Google, which is bundled
  for a different reason: minizen ships its SDK rather than reusing another client.
- `docs/faq.md` — Google moves into the "Working with a default install" list and
  is dropped from the "Others — Google, Groq, Mistral, xAI, Cohere and the rest"
  sentence.

`README.md` already lists Google among the supported providers and is unchanged.

## Testing

One case added to `tests/ai/test_provider_keys.py`, asserting that
`resolve_provider_key(model="google:gemini-2.0-flash")` returns
`ProviderKey(prefix="google", label="Google API key", env_var="GOOGLE_API_KEY")`.

This test is meaningful only once the SDK is bundled: before the dependency change
it fails with `ConfigError`, because `resolve_provider_key` calls the real
`infer_provider_class`. It therefore doubles as the regression guard against the
`google` extra being dropped from `pyproject.toml`.

The existing missing-extra test mocks `infer_provider_class` with an `ImportError`
for `groq` and is unaffected. No new branches are introduced, so the project's
100% coverage gate holds.
