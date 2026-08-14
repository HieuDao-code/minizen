# Shorter Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shorten the digest email by removing the narrative intro paragraph and capping every story summary at one sentence.

**Architecture:** The digest format is defined entirely by `_SYSTEM_PROMPT` in `src/minizen/ai/agent.py` — the AI returns Markdown, and `src/minizen/providers/email/template.py` renders it. So the format change is a prompt edit plus test and fixture updates. No config, no schema change, no rendering logic change.

**Tech Stack:** Python 3.14, pydantic-ai, mistune, pytest, pytest-mock, tox, ruff.

## Global Constraints

- Package manager: `uv`, never `pip`.
- Docstrings required for all modules, functions, methods, and classes. Google style with `Args:` / `Returns:` / `Raises:`, omitting sections that do not apply. Test functions in this repo do not carry docstrings — follow the existing file style.
- Tests: type hints on every test parameter including fixtures; keyword arguments when calling code under test; `arrange` / `act` / `assert` comment sections separated by blank lines, omitting `# arrange` when that section is empty; no module-level constants.
- Commit messages follow Conventional Commits (the repo uses `commitizen`).
- Do not change `AIConfig`, `DigestResult`, or the `_build_article_cards` regex. Those are explicitly out of scope.

---

### Task 1: Rewrite the system prompt

Change the digest format instructions so the AI emits no intro and one sentence per story.

**Files:**
- Modify: `src/minizen/ai/agent.py:18-60` (the `_SYSTEM_PROMPT` string literal)
- Test: `tests/ai/test_agent.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a `_SYSTEM_PROMPT` module-level string containing the exact substrings `"Do not write an introduction"` and `"exactly one sentence"`, and no longer containing `"diverge"`. Task 2 relies on the resulting digest shape (no intro paragraph) but not on this symbol directly.

- [ ] **Step 1: Write the failing tests**

Add these three tests to `tests/ai/test_agent.py`, immediately after `test_system_prompt_requires_every_referenced_id` (which ends at line 201) and before the `# --- max_words_per_article wiring ---` comment:

```python
def test_system_prompt_requires_one_sentence_summary() -> None:
    # assert
    assert "exactly one sentence" in _SYSTEM_PROMPT


def test_system_prompt_forbids_introduction() -> None:
    # assert
    assert "Do not write an introduction" in _SYSTEM_PROMPT


def test_system_prompt_omits_source_divergence_instruction() -> None:
    # assert
    assert "diverge" not in _SYSTEM_PROMPT
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/ai/test_agent.py -k "one_sentence or forbids_introduction or divergence" -v`

Expected: 3 FAILED, all `AssertionError`. The prompt currently says "exactly 2-3 sentences", has no "Do not write an introduction" line, and does contain "diverge".

- [ ] **Step 3: Remove the intro instruction**

In `src/minizen/ai/agent.py`, replace this block (lines 32-35):

```
Start the digest with a short narrative intro paragraph (2-4 sentences). Do not mention
specific articles in the intro.

Then write one section per selected story using this template exactly:
```

with:

```
Do not write an introduction, preamble, or closing paragraph. Start directly with the
first story.

Write one section per selected story using this template exactly:
```

- [ ] **Step 4: Cap the summary at one sentence in the template**

In the same string, replace the summary placeholder (lines 41-42):

```
{2-3 sentence summary. Concise. No bullet points. When a story has multiple sources,
synthesise across them and note where they diverge.}
```

with:

```
{One sentence stating what happened. No bullet points.}
```

This single edit both caps the length and drops the divergence clause.

- [ ] **Step 5: Cap the summary at one sentence in the rules**

Replace this rules line (line 56):

```
- Summary: exactly 2-3 sentences, no lists, no sub-headings.
```

with:

```
- Summary: exactly one sentence, no lists, no sub-headings.
```

Stating the cap in both the template and the rules is deliberate — the prompt already used that redundancy for the 2-3 sentence cap, and it is why the cap holds.

- [ ] **Step 6: Drop the "cohesive" wording**

Replace this line (line 22):

```
3. Write a cohesive Markdown digest following this exact structure.
```

with:

```
3. Write a Markdown digest following this exact structure.
```

"Cohesive" described the narrative flow the intro created; leaving it in makes the prompt pull against the new format.

- [ ] **Step 7: Run the new tests to verify they pass**

Run: `uv run pytest tests/ai/test_agent.py -k "one_sentence or forbids_introduction or divergence" -v`

Expected: 3 PASSED.

- [ ] **Step 8: Run the whole agent test file to check for regressions**

Run: `uv run pytest tests/ai/test_agent.py -v`

Expected: all PASSED. In particular `test_system_prompt_instructs_same_event_clustering`, `test_system_prompt_defines_also_covered_by_template`, `test_system_prompt_selects_primary_source`, and `test_system_prompt_requires_every_referenced_id` must still pass — they are the regression net proving the clustering feature from #29 is undisturbed.

- [ ] **Step 9: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat(ai): drop digest intro and cap summaries at one sentence"
```

---

### Task 2: Update the fixture, template test, and dead CSS

Bring the test fixture in line with the new format and remove the CSS rule that only ever styled the intro.

**Files:**
- Modify: `tests/fixtures/digest_result.md` (full rewrite)
- Modify: `tests/providers/email/test_template.py:36-55` (fixture test) and append one new test
- Modify: `src/minizen/providers/email/template.py:176-181` (delete the `.content > p` rule)

**Interfaces:**
- Consumes: the digest shape produced by Task 1 — no intro paragraph, one-sentence summaries, `Also covered by:` line on multi-source stories.
- Produces: nothing later tasks depend on. This is the final task.

- [ ] **Step 1: Write the failing test**

Append this test to the end of `tests/providers/email/test_template.py`:

```python
def test_render_email_has_no_intro_paragraph_before_first_card() -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "digest_result.md"
    content = fixture_path.read_text()

    # act
    html, _ = render_email(markdown=content)

    # assert
    content_start = html.index('<div class="content">')
    first_card = html.index('<div class="article-card">')
    assert "<p" not in html[content_start:first_card]
```

The assertion is scoped to the span between the content div and the first card on purpose. An unscoped "no `<p>` outside a card" check would fail on the header's own `<p class="header-label">` and `<p class="meta">`, which are legitimate.

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/providers/email/test_template.py::test_render_email_has_no_intro_paragraph_before_first_card -v`

Expected: FAILED with `AssertionError`. The current fixture opens with `Today's digest covers developments across...`, which mistune renders as a `<p>` before the first card.

- [ ] **Step 3: Rewrite the fixture**

Replace the entire contents of `tests/fixtures/digest_result.md` with:

```markdown
**Hacker News**

## [Rust's async story is finally complete](https://blog.rust-lang.org/2026/04/async-maturity)

Rust's async ecosystem has stabilised around tokio and the new standard library async traits after years of fragmentation.

[Comments](https://news.ycombinator.com/item?id=12345)

**Anthropic**

## [Most LLM context goes unused](https://www.anthropic.com/research/context-window-cost)

A joint Anthropic and Stanford paper finds that most real-world tasks use fewer than 10% of available context tokens productively.

Also covered by: [Hacker News](https://news.ycombinator.com/item?id=12346) · [Ars Technica](https://arstechnica.com/ai/2026/04/context-utilization)

[Comments](https://news.ycombinator.com/item?id=12346)

**The Verge**

## [Apple's M4 Ultra is a genuine leap for creative work](https://www.theverge.com/2026/4/25/apple-m4-ultra-review)

The M4 Ultra ships with 256GB unified memory while staying inside the M3 generation's power envelope, which film editors call transformative for 8K RAW workflows.

**The Verge**

## [Platforms quietly dialling back outrage amplification](https://www.theverge.com/2026/4/24/attention-economy-shift)

Several major platforms cut algorithmic amplification of inflammatory content after EU DSA enforcement, trading a 4% drop in session time for an 11% gain in 30-day retention.

**Ars Technica**

## [Webb finds unusual chemistry on TRAPPIST-1e](https://arstechnica.com/science/2026/04/webb-trappist-chemistry)

The James Webb Space Telescope detected sulfur dioxide and water vapour with an anomalous sulfur isotope ratio on TRAPPIST-1e after combining 47 transit observations.
```

Two things changed beyond shortening. The old fixture used a `[Read →](url) · [Comments](url)` line that the prompt has not produced since #29 — the title is the link now, so that line is gone. And the second story gained an `Also covered by:` line so the fixture actually exercises the clustered multi-source path.

- [ ] **Step 4: Update the reading-time assertion in the existing fixture test**

The rewritten fixture is 171 words, and `_reading_time` computes `max(1, ceil(words / 200))`, so the rendered header now says `~1 min read`.

In `tests/providers/email/test_template.py`, inside `test_render_email_with_fixture_digest`, change:

```python
    assert "~3 min read" in html
```

to:

```python
    assert "~1 min read" in html
```

Leave every other assertion in that test alone — `Rust`, `Most LLM`, `Apple`, `Platforms`, and `Webb` all still appear in the new fixture, and the palette assertions are unaffected.

- [ ] **Step 5: Run both fixture tests to verify they pass**

Run: `uv run pytest tests/providers/email/test_template.py -k "fixture or intro_paragraph" -v`

Expected: 2 PASSED.

- [ ] **Step 6: Delete the dead CSS rule**

In `src/minizen/providers/email/template.py`, delete this block (lines 176-181):

```
    .content > p {{
      font-size: 16px;
      line-height: 1.8;
      color: {_TEXT};
      margin: 0 0 24px;
    }}
```

This rule styled the intro paragraph and nothing else. Every other `<p>` in the email sits inside `.article-card` or `.more-links`, both of which have their own rules, so with the intro gone this selector matches nothing.

- [ ] **Step 7: Run the full test suite**

Run: `uv run pytest -v`

Expected: all PASSED. `test_render_email_does_not_use_old_palette` and the `_TEXT` colour assertions still pass — `_TEXT` remains in use by `body`, `.article-card h2`, and `.article-card p`.

- [ ] **Step 8: Run the linters**

Run: `uv run ruff check && uv run ruff format --check`

Expected: no errors. If `ruff format --check` reports a diff, run `uv run ruff format` and re-run the check.

- [ ] **Step 9: Commit**

```bash
git add tests/fixtures/digest_result.md tests/providers/email/test_template.py src/minizen/providers/email/template.py
git commit -m "test: update digest fixture for shorter format"
```

---

## Verification

After both tasks, confirm the change end to end:

```bash
uv run pytest -v
uv run ruff check
```

Optionally preview a real digest against your configured Miniflux instance:

```bash
uv run minizen digest preview
```

Expect the output to start directly with the first feed-name badge — no intro paragraph — and every story summary to be a single sentence.
