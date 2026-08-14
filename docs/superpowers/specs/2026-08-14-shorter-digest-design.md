# Shorter digest — design

**Date:** 2026-08-14
**Status:** Approved

## Problem

The digest email is longer than it needs to be. Two things pad it: a 2-4 sentence
narrative intro paragraph before the first story, and a 2-3 sentence summary on every
story. A curated digest should let the reader scan headlines and decide what to open —
the linked articles carry the detail.

## Goal

- No intro paragraph. The email starts with the first story.
- Every story summary is exactly one sentence.

## Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Fixed or configurable | Fixed | No new config surface, defaults, loader tests, docs, or setup-wizard questions. A knob can be added later if the shorter form proves too terse. |
| Clustered stories | State what happened only | Dropping "note where they diverge" keeps every story uniformly one sentence. The "Also covered by" links let the reader compare sources directly. |
| Enforcement | Prompt only | No post-processing guard and no structured-output rewrite. Failure mode is mild — an occasional two-sentence summary, not a broken email. |

## Scope

Everything lands in the system prompt plus test/fixture updates. Not in scope:

- Config model changes (`AIConfig` is untouched; `top_n` remains the reader's knob).
- `DigestResult` schema changes — the agent still returns Markdown plus article IDs.
- Refactoring `_build_article_cards`'s `<p><strong>…</strong></p>` regex into structured
  output. That is a worthwhile change but deserves its own spec.

## Design

### 1. System prompt (`src/minizen/ai/agent.py`, `_SYSTEM_PROMPT`)

Three edits, plus one wording fix.

**Drop the intro.** Replace the current instruction:

> Start the digest with a short narrative intro paragraph (2-4 sentences). Do not mention
> specific articles in the intro.

with an explicit negative instruction:

> Do not write an introduction, preamble, or closing paragraph. Start directly with the
> first story.

Telling the model to omit the intro works better than silently deleting the request,
which otherwise leaves it free to write a preamble out of habit.

**One sentence per story.** Two coordinated changes:

- Template placeholder becomes `{One sentence stating what happened. No bullet points.}`
- Rules line becomes `Summary: exactly one sentence, no lists, no sub-headings.`

Stating the cap in both the template and the rules is deliberate. The current prompt
already does this for its 2-3 sentence cap, and that redundancy is why the cap holds.

**Drop the divergence clause.** Remove "When a story has multiple sources, synthesise
across them and note where they diverge" from the template placeholder.

**Wording fix.** The prompt's step 3 says "Write a *cohesive* Markdown digest". "Cohesive"
described the narrative flow the intro created; drop the word so the prompt does not pull
against the new format.

Unchanged: grouping rules, primary-source selection, the bold feed-name line, the linked
title, the "Also covered by" line, the Comments link, and the contract that returned
article IDs cover every referenced source.

### 2. Rendering (`src/minizen/providers/email/template.py`)

No logic change required. `_build_article_cards` splits the rendered HTML on the
`<p><strong>Feed Name</strong></p>` badge pattern and treats `parts[0]` as intro content.
With no intro, `parts[0]` is an empty string and cards render normally.

One cleanup falls out: the `.content > p` CSS rule styled the intro paragraph only. Every
other `<p>` is inside `.article-card` or `.more-links`, so the rule matches nothing once
the intro is gone. Delete it.

The header block (label, "Your Daily Zen", date, reading time) and the "More to read"
list are unchanged. Reading time will now typically render as "~1 min read", which is
accurate.

### 3. Test fixture (`tests/fixtures/digest_result.md`)

Hand-write the updated fixture (no AI call): no intro line, one sentence per summary.

The fixture is already stale — it uses a `[Read →](url) · [Comments](url)` line that the
prompt has not produced since the story-clustering change (#29), and contains no
`Also covered by` line. Since it is being rewritten anyway, bring it in line with what
the prompt emits today, including at least one clustered multi-source story. This makes
`test_render_email_with_fixture_digest` exercise the real format again.

### 4. Tests

New tests follow the existing `test_system_prompt_*` substring-assertion pattern in
`tests/ai/test_agent.py`:

- prompt instructs exactly one sentence per summary
- prompt forbids an introduction or preamble
- prompt no longer mentions noting where sources diverge

In `tests/providers/email/test_template.py`:

- rendering the updated fixture emits no `<p>` between the opening `<div class="content">`
  and the first `<div class="article-card">`, guarding the no-intro contract end to end.
  The assertion must be scoped to that span: the header block legitimately contains
  `<p class="header-label">` and `<p class="meta">`.

Existing assertions on same-event clustering, `Also covered by:`, primary-source
selection, and article-ID coverage stay untouched. They are the regression net proving
this change does not disturb #29.

## Risks

The model may occasionally emit two sentences despite the cap. Accepted: the email still
renders correctly and the result is still shorter than today. If it proves frequent, a
follow-up can add a truncation guard or move to structured output.
