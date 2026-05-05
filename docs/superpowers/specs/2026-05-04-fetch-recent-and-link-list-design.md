# Design: Fetch Recent Articles & Link List

**Date:** 2026-05-04

## Problem

The current pipeline fetches all *unread* Miniflux entries with no time limit. This creates two issues:

1. Articles read the night before a digest run are excluded from summaries, even if they are relevant and recent.
2. Unread articles accumulate indefinitely — the pool grows stale over time.

## Goals

- Fetch all articles published in the last 24 hours, regardless of read status.
- Show full AI summaries for the top N selected articles.
- Show all remaining fetched articles as a compact link list at the bottom of the digest.
- Stop marking articles as read — the user manages read state in their RSS reader.

## Design

### Fetch layer (`providers/rss/miniflux.py`)

Rename `fetch_unread()` to `fetch_recent()`. It calls the Miniflux API with an `after` parameter set to 24 hours ago (Unix timestamp), with no status filter. This returns all articles published in the last 24h, read or unread.

Remove `mark_as_read()` entirely — it is no longer needed.

### Pipeline (`core/pipeline.py`)

1. Call `fetch_recent()` instead of `fetch_unread()`.
2. Remove the `rss.mark_as_read(...)` call — the pipeline ends after sending the email.
3. Pass both `result` (the `DigestResult`) and the full `articles` list to `render_email()`.

### Template (`providers/email/template.py`)

`render_email()` gains a second parameter: `all_articles: list[Article]`.

After rendering the main digest cards (top N with full summaries), the template appends a "More to read" section. This section lists every article whose ID is not in `result.articles_used`, formatted as a compact `<ul>` of links — each item is the article title linked to its URL. No summaries, no feed badges.

### AI agent (`ai/agent.py`)

No changes. `DigestResult.articles_used` already captures the IDs of selected articles, which is all the template needs to compute the remainder.

### Documentation

- `docs/how_it_works.md`: Update the pipeline description and Mermaid diagram to reflect the new flow — replace "unread articles" with "last 24h articles", remove the "mark as read" step, mention the link list in the render step.
- `docs/faq.md`: Update "What happens if there are no unread articles?" to "What happens if there are no recent articles?" with updated wording to match the new behaviour.

## Non-goals

- Making the 24h window configurable — hardcoded is sufficient for a daily digest.
- Capping the link list — all non-selected articles from the 24h window are shown.
- Any changes to the AI agent's selection logic or output format.
