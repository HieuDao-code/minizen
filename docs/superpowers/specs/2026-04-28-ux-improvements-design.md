# UX Improvements Design

**Date:** 2026-04-28
**Branch:** feat/ux

## Overview

Improve the minizen digest experience across two surfaces:

1. **Email** — enforce a consistent, newsletter-style per-article format and apply a refined editorial colour palette with article cards.
2. **Config** — raise the default article count from 5 to 10 to produce a fuller digest out of the box.

Terminal output remains plain text (no rich rendering).

---

## Scope

### 1. Default article count

Change `DEFAULT_TOP_N` in `src/minizen/config/defaults.py` from `5` to `10`.

No other files need changing — `AIConfig` already reads from this constant.

---

### 2. Article model — `comments_url`

Add an optional `comments_url: str | None` field to `Article` in `src/minizen/providers/rss/miniflux.py`. The Miniflux API returns `comments_url` on each entry (empty string when absent). Map it during `fetch_unread`:

```python
comments_url=entry.get("comments_url") or None,
```

`None` when the field is absent or an empty string.

---

### 3. AI system prompt — newsletter template

Update `_SYSTEM_PROMPT` in `src/minizen/ai/agent.py` to enforce this per-article Markdown template:

```
**{feed_name}**

## [Article Title](url)

2–3 sentence summary.

[Read →](url) · [Comments](comments_url)
```

Rules baked into the prompt:
- Start with a short narrative intro paragraph (2–4 sentences, no article references).
- One section per selected article, following the template exactly.
- Omit the `[Comments]` link when `comments_url` is not provided for that article.
- Each title must be a Markdown link to `url`.
- Feed name rendered as bold text above the title (not a heading).
- Summary: 2–3 sentences, concise, no bullet points.

The articles text passed to the agent gains a `Comments URL` line per article so the AI knows when one is available.

---

### 4. Email HTML — card layout and colour palette

#### Colour palette

| Token         | Value       | Usage                                     |
|---------------|-------------|-------------------------------------------|
| `bg`          | `#EEF2F7`   | Page background                           |
| `card-bg`     | `#FFFFFF`   | Article card background                   |
| `text`        | `#1E2D3D`   | Body text, titles                         |
| `accent-blue` | `#2D7DD2`   | Links, Read button                        |
| `accent-orange` | `#D4622A` | Feed name badge, section dividers         |
| `border`      | `#D4DCE8`   | Card borders, `<hr>`                      |
| `muted`       | `#5A6A7A`   | Meta text, footer                         |
| `header-bg`   | `#1E2D3D`   | Email header background                   |
| `header-text` | `#FFFFFF`   | Email header text                         |

#### Layout structure

```
┌─────────────────────────────────────┐
│  HEADER (dark navy bg, white text)  │
│  minizen · Your Daily Zen · date    │
├─────────────────────────────────────┤
│  Intro paragraph (narrative text)   │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ FEED NAME (orange badge)      │  │
│  │                               │  │
│  │ Article Title (bold, blue)    │  │
│  │                               │  │
│  │ Summary text here. Two or     │  │
│  │ three concise sentences.      │  │
│  │                               │  │
│  │ [Read →]  [Comments]          │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ ... next article card ...     │  │
│  └───────────────────────────────┘  │
│                                     │
├─────────────────────────────────────┤
│  FOOTER (muted, centred)            │
└─────────────────────────────────────┘
```

#### Card styling

Each `<h2>` block (article section) in the rendered HTML is wrapped in a card `<div>`:

- Background: `#FFFFFF`
- Border: `1px solid #D4DCE8`
- Border-radius: `12px`
- Padding: `24px`
- Margin-bottom: `16px`

The `**feed_name**` bold text above each `<h2>` renders as a small uppercase label in `#D4622A`.

The `<h2>` title link renders in `#2D7DD2` (blue), no underline.

Read and Comments links render as small inline pill-style anchors in `#2D7DD2`.

The header switches from the warm gradient to a solid dark navy (`#1E2D3D`) background with white text.

#### Implementation approach

`render_email` in `src/minizen/providers/email/template.py` currently passes AI Markdown through `mistune.html()` and injects it verbatim. Post-processing is added after `mistune` renders to:

1. Wrap each `<h2>…</h2>` block and its following siblings (up to the next `<h2>` or end) in a card `<div>`.
2. Convert the `<strong>` immediately preceding each `<h2>` (the feed name) into a styled badge `<span>`.

All colour values are defined as Python constants at the top of the module for easy future changes.

---

## Files changed

| File | Change |
|------|--------|
| `src/minizen/config/defaults.py` | `DEFAULT_TOP_N = 10` |
| `src/minizen/providers/rss/miniflux.py` | Add `comments_url: str \| None` to `Article`; map in `fetch_unread` |
| `src/minizen/ai/agent.py` | Update `_SYSTEM_PROMPT` with newsletter template; pass `comments_url` in articles text |
| `src/minizen/providers/email/template.py` | New colour palette constants; card wrapping post-processor; updated header/footer HTML |

---

## Testing

- `test_defaults.py` — update `DEFAULT_TOP_N` assertion from `5` to `10`.
- `test_miniflux.py` — add cases: `comments_url` mapped when present; `None` when absent/empty.
- `test_template.py` — assert card `<div>` wrapping present; assert colour constants used in output; assert feed name badge rendered; assert old palette values absent.
- `test_agent.py` — assert `comments_url` line present in articles text passed to agent.

No new dependencies required.
