# Interest Profile Feature Design

**Date:** 2026-05-06

## Overview

Add a structured interest profile to minizen's config so the AI agent can prioritise articles the user cares about and skip topics they don't want. Both fields are optional — existing users see no behaviour change.

## Config Model

Add two optional fields to `AIConfig` in `src/minizen/config/models.py`:

```python
interests: list[str] = Field(default_factory=list, description="Topics to prioritise.")
avoid: list[str] = Field(default_factory=list, description="Topics to avoid.")
```

Resulting TOML shape:

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
interests = ["Rust", "AI safety", "climate tech"]
avoid = ["sports", "celebrity news", "crypto"]
```

Both fields default to `[]`. No migration needed — configs without these fields parse fine.

## Setup Wizard

**Interactive mode** — two new optional prompts added after the existing AI prompts:

```
Topics you're interested in (comma-separated, Enter to skip):
Topics to avoid (comma-separated, Enter to skip):
```

Pressing Enter skips the field (empty list). Input is split on commas and each item stripped of whitespace.

**Non-interactive mode** — two new CLI flags:

```
--interests "Rust,AI safety,climate tech"
--avoid "sports,crypto"
```

Both optional; absent flags produce empty lists.

## AI Agent

`DigestAgent.__init__` accepts `interests: list[str]` and `avoid: list[str]` parameters (both default to `[]`). When either list is non-empty, a preference block is appended to `_SYSTEM_PROMPT`:

```
User preferences:
- Prioritise articles about: Rust, AI safety, climate tech
- Avoid articles about: sports, celebrity news, crypto
```

Only the non-empty lists produce a line. When both are empty the system prompt is unchanged.

`run_pipeline` passes `settings.ai.interests` and `settings.ai.avoid` through to `DigestAgent`.

## Error Handling

No new error cases. Empty strings after stripping are dropped from the parsed list. The feature is purely additive — all changes are backwards-compatible.

## Testing

- `AIConfig` parses correctly with and without the new fields.
- `DigestAgent` injects the preference block when lists are non-empty, leaves prompt unchanged when both are empty.
- Setup wizard parses comma-separated input into lists correctly, handles empty input.
- `run_pipeline` passes interests/avoid through to the agent.
