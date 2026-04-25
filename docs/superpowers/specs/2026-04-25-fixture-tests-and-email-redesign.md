# Fixture-Based Integration Tests & Email Template Redesign

## Goal

Add realistic fixture files and fixture-based integration tests covering RSS parsing, digest rendering, and the full pipeline. Simultaneously redesign the email template with a calm sage-and-linen palette.

## Architecture

Two workstreams that share the same fixture files:

1. **Fixtures + tests** — hand-crafted realistic fixture files drive three new integration tests added to existing test files. No live API calls.
2. **Email redesign** — retheme `template.py` CSS in-place. Remove dark mode block. Apply Option B sage & warm neutral palette.

A live capture run (post-implementation) will validate the fixture files against real Miniflux and LLM output and update them if needed.

## Fixture Files

### Location

```
tests/fixtures/
    miniflux_response.json
    digest_result.md
```

### `miniflux_response.json`

Realistic Miniflux `get_entries` API response shape: `{"total": 5, "entries": [...]}`.

Five entries across three feeds. Each entry must have:
- `id` (int)
- `title` (str, realistic headline)
- `url` (str, realistic URL)
- `content` (str, 2–3 paragraphs of HTML, not just `<p>Body</p>`)
- `feed`: `{"title": str}` (one of three feed names)
- `published_at` (str, ISO 8601 with Z suffix, varied dates)

### `digest_result.md`

Realistic LLM-generated digest markdown. Structure:
- Short intro paragraph (~2 sentences)
- 4–5 `##` section headings (article titles or themed groupings)
- 3–4 sentence summary per section
- At least 3 markdown links `[text](url)`
- Total: ~450–550 words (so `_reading_time()` returns ≥ 2 min)

Plain text — no frontmatter, no metadata.

## Integration Tests

All tests are added to existing test files. No new test files created.

### `tests/providers/rss/test_miniflux.py`

**`test_fetch_unread_with_fixture_data`**

- Load `tests/fixtures/miniflux_response.json` via `Path` + `json.loads`
- Patch `minizen.providers.rss.miniflux.miniflux.Client` to return the fixture dict
- Call `provider.fetch_unread()`
- Assert:
  - `len(articles) == 5`
  - All three feed names appear across articles
  - All `published_at` values are timezone-aware datetimes (UTC)
  - No article has an empty `title` or `url`

### `tests/providers/email/test_template.py`

**`test_render_email_with_fixture_digest`**

- Load `tests/fixtures/digest_result.md` via `Path.read_text()`
- Call `render_email(markdown=content)`
- Assert on `html`:
  - Each `##` heading from the markdown appears in the HTML output
  - `#7A9E7E` (sage accent) appears in the CSS
  - `#F2EFE9` (linen background) appears in the CSS
  - `min read` appears (reading time rendered)
- Assert `plain_text == content` (unchanged passthrough)

### `tests/core/test_pipeline.py`

**`test_pipeline_sends_email_with_fixture_data`**

- Load both fixtures
- Patch `minizen.core.pipeline.MinifluxProvider` — `fetch_unread` returns 5 `Article` objects built from the JSON fixture
- Patch `minizen.core.pipeline.DigestAgent` — `run` returns `DigestResult(markdown=<fixture markdown>, articles_used=[1,2,3,4,5])`
- Patch `minizen.core.pipeline.EmailProvider` — capture `send()` call args
- Patch `minizen.core.pipeline.render_email` to call the real function (no mock — use `wraps`)
- Call `run_pipeline(settings=mock_settings, dry_run=False)`
- Assert:
  - `EmailProvider.send` called once
  - `subject` contains today's date string
  - `html` contains at least one `##` heading from the fixture markdown
  - `MinifluxProvider.mark_as_read` called with all 5 article IDs

## Email Template Redesign

### Palette (Option B — Sage & Warm Neutral)

| Token | Value | Usage |
|---|---|---|
| Linen background | `#F2EFE9` | `body` background |
| Card | `#FAFAF8` | `.wrapper` background |
| Body text | `#2E2A25` | `body`, `p`, `ul`, `ol` |
| Sage accent | `#7A9E7E` | `h2` border-left, `.footer a` |
| Sage link | `#6B8F6E` | `a` color |
| Dark outline | `#3A3A3A` | `hr`, borders |
| Muted text | `#6B6560` | `.content em`, `.footer` |
| Header gradient | `#F2EFE9 → #C8B89A → #9E8A72` | `.header` background |
| Header text | `#2E2A25` | `.header h1`, `.header p` |

### Changes to `template.py`

- Replace all current color values with the palette above
- Remove the entire `@media (prefers-color-scheme: dark)` block
- Header gradient: warm linen to warm taupe (`#F2EFE9 → #C8B89A → #9E8A72`)
- `h2` left border: `#7A9E7E`
- Links (`a`): `#6B8F6E`
- Footer link: `#7A9E7E`
- `body` background: `#F2EFE9`
- `.wrapper` background: `#FAFAF8`
- Body text everywhere: `#2E2A25`

No structural HTML changes — CSS values only.

## What This Does Not Cover

- Live API capture (post-implementation manual step)
- Changes to `MinifluxProvider`, `DigestAgent`, or `EmailProvider` logic
- New CLI commands or flags
- Dark mode support
