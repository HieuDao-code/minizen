# Same-event story clustering

**Date:** 2026-07-24
**Status:** Approved (design)

## Problem

minizen curates unread RSS articles into a top-N digest, but treats every article
independently. When several feeds cover the same event, the digest lists the story
multiple times — once per feed. This directly undercuts minizen's promise of
"a quieter way to stay informed" and wastes the limited `top_n` slots on duplicates.

Comparable premium tools (Readless, Feedly Leo, Brief Digest) differentiate on exactly
this: collapsing multi-source coverage of one event into a single entry attributed to
every source. minizen is unusually well-positioned to do the same because its agent
already receives every candidate article in a single prompt, so clustering can happen in
that same LLM call — no embeddings, no vector store, no new dependencies.

## Goal

When multiple feeds cover the same specific real-world event, minizen collapses them into
one story: a primary headline plus an "Also covered by" line listing the other sources.
`top_n` now counts distinct **stories** rather than articles.

Non-goals (deliberately out of scope):

- Topical/thread grouping across distinct developments — only same-event coverage merges.
- A separate "cluster aggressiveness" configuration knob — `top_n` stays the single dial.
- Local dedup state or marking articles read in Miniflux — untouched.
- Email-template CSS work for the new line — it renders as a normal paragraph.

## Design

### Clustering behavior

- Merge only when articles cover the **same specific real-world event** (e.g. the same
  product launch or announcement). Distinct developments stay as separate stories.
- For each story, the model picks the most complete/authoritative source as the
  **primary**; the rest become secondary "Also covered by" sources.
- The per-story summary synthesizes across all sources and notes where they diverge.
- `top_n` limits the number of stories after clustering. A 3-source story counts as 1.

### Rendered format

Single-source stories render exactly as today (no visual change when there is no
overlap). A multi-source story adds one line, between the summary and the `[Comments]`
link:

```markdown
**The Verge**

## [OpenAI ships new model](https://theverge.com/...)

A merged 2-3 sentence summary drawing on all the coverage, noting where sources differ.

Also covered by: [Ars Technica](url) · [TechCrunch](url)

[Comments](url)
```

- The "Also covered by" line is omitted entirely for single-source stories.
- It sits after the summary and before the optional `[Comments]` link.
- The primary source remains the bold feed-name line and the linked `##` heading, so the
  email template's card detection (`_build_article_cards`, splitting on
  `<p><strong>…</strong></p>`) keeps working with no change.

## Components changed

### 1. `ai/agent.py` — system prompt (core of the change)

- Add a clustering step to `_SYSTEM_PROMPT`: group articles covering the same specific
  real-world event into one story; only merge same-event coverage; keep distinct
  developments separate; pick the most complete/authoritative source as primary.
- Update the per-story render template to append the `Also covered by: …` line after the
  summary and before `[Comments]`, omitted when a story has a single source.
- Summary instruction: synthesize across sources and note divergences.
- **Critical rule:** `articles_used` must list the IDs of *every* article referenced in
  any story — the primary *and* every "Also covered by" source. This keeps secondary
  sources out of the "More to read" list (see Data flow).

### 2. `ai/agent.py` — user prompt & docstrings

- `run()`'s user prompt changes from "top N articles" to "top N **stories**".
- Docstrings referring to article selection updated to speak of stories where relevant.

### 3. `config/models.py`

- `AIConfig.top_n` field description updated to "Maximum number of stories (after
  deduplication) to include." No new field; no config-format change; existing configs
  keep working unchanged.

### 4. `providers/email/template.py`

- **No structural change.** The "Also covered by" line renders as a normal paragraph
  inside the article card via mistune. Optional CSS styling is out of scope.

## Data flow

Unchanged pipeline: `fetch → agent → render_email(result.markdown, extra_articles=…) →
send`. `DigestResult` keeps its shape (`markdown`, `articles_used`). The only difference
is that `articles_used` now spans every source across every cluster.

The `extra_articles` list ("More to read") is computed at `pipeline.py:52-53` as
`fetched − articles_used`. Because secondary sources are included in `articles_used`, they
are correctly excluded from "More to read" rather than appearing as if unused.

## Error handling

No new failure modes:

- Over-merging or under-merging is a soft quality outcome, not an exception — the existing
  `AIError` path is unchanged.
- If the model omits a secondary source's ID from `articles_used`, that article merely
  reappears in "More to read". Graceful degradation, no crash.

## Testing

- The built system prompt contains the clustering guidance and the "Also covered by"
  template.
- `run()`'s user prompt says "stories" and includes `top_n`.
- Plumbing test: an `articles_used` set that includes a secondary-source ID excludes that
  article from `extra_articles` at the pipeline level.
- Existing agent/pipeline tests updated for the new wording.

Tests follow project conventions: type-hinted params, keyword arguments, `# arrange /
# act / # assert` sections, `assert_called_once_with(...)`, and module-path patching where
functions are used.
