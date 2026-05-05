# Language Preservation & Word Limit Design

**Date:** 2026-05-05
**Status:** Approved

## Overview

Two configurable improvements to the AI digest agent:

1. **Summary language** — the digest can either match each article's original language (`"auto"`) or use a user-specified language for all summaries.
2. **Word limit per article** — article content is hard-truncated at a configurable word count before being sent to the LLM, reducing token usage.

Both features are opt-in via new fields in the `[ai]` config section, with defaults that preserve existing behaviour.

---

## Config & Models

Two new fields in `AIConfig` (`src/minizen/config/models.py`):

| Field | Type | Default | Description |
|---|---|---|---|
| `summary_language` | `str` | `"auto"` | Language for summaries. `"auto"` matches the article's language; any other value (e.g. `"English"`) forces all summaries into that language. |
| `max_words_per_article` | `int \| None` | `None` | Maximum words of article content sent to the LLM. `None` disables truncation. |

Existing configs require no changes.

---

## Agent changes (`src/minizen/ai/agent.py`)

### Constructor

`DigestAgent.__init__` gains two new keyword-only parameters:

```python
def __init__(self, *, model: str, top_n: int, summary_language: str = "auto", max_words_per_article: int | None = None) -> None:
```

Both are stored as instance attributes and used in `run()`.

### System prompt language rule

One new rule is appended to `_SYSTEM_PROMPT` based on `summary_language`:

- `"auto"`: *"Write each article's summary in the same language the article is written in."*
- Any other value: *"Write all summaries in {summary_language}."*

The rule is injected dynamically at init time so `_SYSTEM_PROMPT` stays a module-level template with a `{language_rule}` placeholder.

### Content truncation helper

A module-level helper:

```python
def _truncate_words(html: str, max_words: int) -> str
```

Uses `html.parser` (stdlib) to strip HTML tags, splits on whitespace, and joins the first `max_words` words. Returns the stripped plain text.

In the `articles_text` loop inside `run()`, when `max_words_per_article` is set:

```python
content = _truncate_words(a.content, self._max_words_per_article)
```

Otherwise `a.content` is used as-is.

---

## Pipeline & CLI wiring

`run_pipeline()` (`src/minizen/core/pipeline.py`) and the `send_test`/`preview` commands (`src/minizen/cli/commands/digest.py`) both construct `DigestAgent`. Each call is updated to forward the two new settings:

```python
DigestAgent(
    model=settings.ai.model,
    top_n=settings.ai.top_n,
    summary_language=settings.ai.summary_language,
    max_words_per_article=settings.ai.max_words_per_article,
)
```

No other pipeline or CLI logic changes.

---

## Testing

### `tests/ai/test_agent.py`

New tests for `_truncate_words`:

- HTML tags are stripped before word counting.
- Content at or under the limit has all words preserved (HTML is stripped but no words are cut).
- Content over the limit is truncated at exactly `max_words` words.
- `None` limit results in full content passed as-is (tested via agent integration, not the helper directly).

New tests for the language rule in the system prompt:

- `summary_language="auto"` produces a prompt containing the auto-language instruction.
- `summary_language="English"` produces a prompt containing the specific-language instruction.

Existing agent constructor calls updated to pass `summary_language` and `max_words_per_article`.

### `tests/core/test_pipeline.py` and `tests/cli/commands/test_digest.py`

`DigestAgent` mock constructor assertions updated to expect the two new keyword arguments. No new behaviour tested — wiring only.

---

## Documentation

`docs/configuration.md` — add the two new fields to the `[ai]` section table and the example TOML block.
