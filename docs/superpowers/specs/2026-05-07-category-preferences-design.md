# Category Preferences Design

**Date:** 2026-05-07
**Status:** Approved

## Overview

Add a `preferred_categories` field to `[ai]` config so the AI prioritises articles from certain Miniflux categories when selecting the top N. This is a soft hint — the AI weighs category preference alongside article quality rather than enforcing hard quotas.

## Config

Add `preferred_categories: list[str]` to `AIConfig` alongside the existing `interests` and `avoid` fields:

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
preferred_categories = ["Tech", "Science"]  # optional, Miniflux category names
```

Categories are matched by name (freeform strings). An empty list (the default) means no category preference. The field is fully optional — existing configs without it work unchanged.

## Article model

Add `category: str` to the `Article` pydantic model in `providers/rss/miniflux.py`. The value is extracted from `entry["feed"]["category"]["title"]` in the existing entry response — no additional API calls are needed. If the field is absent (feed has no category assigned), it falls back to `""`.

## AI prompt

`_build_system_prompt` gains a `preferred_categories` parameter. When the list is non-empty, the user-preferences block (already used for `interests`/`avoid`) gains an extra line:

```
- Prefer articles from these Miniflux categories (in order of preference): Tech, Science
```

The article text block sent to the AI gains a `Category: {a.category}` line so the AI can match articles to the preference list.

## Pipeline wiring

`DigestAgent.__init__` gains a `preferred_categories` parameter, threaded through `run_pipeline` from `settings.ai.preferred_categories`, following the exact same pattern as `interests` and `avoid`.

## Documentation

- Add `preferred_categories` row to the `[ai]` table in `docs/configuration.md`.
- Add a "Category preferences" subsection (mirroring the existing "Interest profile" subsection) with an example TOML block and explanation.
- Update the config template in the manual setup section to include a commented-out `preferred_categories` example.

## Error handling

No validation of category names against the Miniflux server — unknown names are silently ignored by the AI. This keeps the implementation simple and avoids an extra API call at startup.

## Testing

- `AIConfig` accepts and defaults `preferred_categories`.
- `_build_system_prompt` includes the preference line when `preferred_categories` is non-empty, and omits it when empty.
- `Article` extracts `category` from entry data and falls back to `""` when absent.
- `MinifluxProvider.fetch_recent` maps `entry["feed"]["category"]["title"]` to `article.category`.
- `DigestAgent` passes `preferred_categories` into the system prompt.
- `run_pipeline` threads `preferred_categories` from settings to the agent.
