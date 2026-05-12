---
title: "More to Read" Section — Feed Name Labels
date: 2026-05-11
branch: feat/all-resources
---

## Goal

Upgrade the "More to Read" section at the bottom of the digest email so that each article link is preceded by a small feed-name badge, making the secondary article list visually consistent with the main article cards above it.

## Current State

`_build_more_links` in `src/minizen/providers/email/template.py` renders extra articles (those not selected by the AI for full summaries) as a bare `<ul>` of linked titles:

```html
<li><a href="...">Article Title</a></li>
```

## Target State

Each list item stacks a feed-name badge above the linked title:

```html
<li>
  <span class="feed-badge">Feed Name</span>
  <a href="...">Article Title</a>
</li>
```

## Changes

### `_build_more_links` (Python)

- Use `a.feed_name` to emit a `<span class="feed-badge">` before the `<a>` inside each `<li>`.
- No change to filtering logic (URL scheme check stays).

### CSS (inline in `render_email`)

Two additions to the `.more-links` block:

```css
.more-links li { margin-bottom: 12px; }
.more-links .feed-badge { display: block; }
```

`display: block` makes the badge stack above the link. `margin-bottom` gives items breathing room.

## What Does Not Change

- Section title: "More to read"
- `<ul>/<li>` structure
- `.feed-badge` base styles (orange, uppercase, 11 px)
- Pipeline, CLI, AI agent, `Article` model

## Scope

Two edits in `src/minizen/providers/email/template.py`:
1. The `_build_more_links` function body.
2. The CSS string inside `render_email`.
