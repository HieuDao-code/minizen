# Same-event story clustering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When multiple feeds cover the same real-world event, minizen collapses them into one digest story (primary headline + "Also covered by" line), and `top_n` counts stories instead of articles.

**Architecture:** The change is entirely prompt-level. The `DigestAgent` already sends every candidate article to the LLM in a single call, so clustering is instructed in `_SYSTEM_PROMPT` and the story-count framing moves into the user prompt. `DigestResult` keeps its shape; the only behavioral shift is that `articles_used` must now enumerate every referenced source (primary + secondary), which the existing `extra_articles = fetched − articles_used` diff in the pipeline already consumes correctly.

**Tech Stack:** Python 3, pydantic-ai (`Agent`, structured `DigestResult` output), pytest + pytest-mock, mistune (email rendering — untouched here).

## Global Constraints

- Test coverage must stay at 100% — `pyproject.toml` sets `--cov-fail-under=100`. Every new/changed line must be exercised by a test.
- Docstrings: Google-style with `Args:`/`Returns:`/`Raises:` where applicable; omit irrelevant sections (project CLAUDE.md).
- Test conventions (project CLAUDE.md): type-hinted params (fixtures included), keyword arguments when calling code under test, `assert_called_once_with(...)` (never bare `assert_called_once()`), `# arrange` / `# act` / `# assert` sections separated by blank lines, no module-level constants in test files, and `mocker.patch` targets the module where the name is *used* (e.g. `minizen.ai.agent.Agent`).
- Run tests with: `uv run pytest`
- Lint/type gate before commit: `uv run ruff check` and `uv run ruff format --check`.
- Scope: this plan touches only `_SYSTEM_PROMPT`, the `run()` user prompt, and the `top_n` field description. No email-template CSS, no local dedup state, no Miniflux read-status changes.

---

### Task 1: Instruct same-event clustering in the system prompt

Rewrite `_SYSTEM_PROMPT` so the agent groups same-event articles into one story, renders a primary source with an optional "Also covered by" line, and returns every referenced article ID.

**Files:**
- Modify: `src/minizen/ai/agent.py` (the `_SYSTEM_PROMPT` module constant, lines 18-43)
- Test: `tests/ai/test_agent.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `_SYSTEM_PROMPT` (module-level `str`) now contains same-event grouping rules, the "Also covered by" render template, and the rule that returned IDs include primary + secondary sources. `_build_system_prompt(...)` still returns `_SYSTEM_PROMPT` verbatim when all preference lists are empty (unchanged contract — existing tests depend on it).

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/ai/test_agent.py` (place them after the existing `_truncate_words` import block usage, near the other prompt tests):

```python
def test_system_prompt_instructs_same_event_clustering() -> None:
    # assert
    assert "same specific real-world event" in _SYSTEM_PROMPT


def test_system_prompt_defines_also_covered_by_template() -> None:
    # assert
    assert "Also covered by:" in _SYSTEM_PROMPT


def test_system_prompt_selects_primary_source() -> None:
    # assert
    assert "primary source" in _SYSTEM_PROMPT


def test_system_prompt_requires_every_referenced_id() -> None:
    # assert
    assert "every article you referenced" in _SYSTEM_PROMPT
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/ai/test_agent.py -k "clustering or also_covered_by or primary_source or referenced_id" -v`
Expected: FAIL — the four assertions fail because the current `_SYSTEM_PROMPT` contains none of those phrases.

- [ ] **Step 3: Replace `_SYSTEM_PROMPT`**

In `src/minizen/ai/agent.py`, replace the entire `_SYSTEM_PROMPT` string (lines 18-43) with:

```python
_SYSTEM_PROMPT = """\
You are a personal news curator. You receive a list of unread articles and must:
1. Group articles that cover the same specific real-world event into a single story.
2. Select the top N most important and interesting stories.
3. Write a cohesive Markdown digest following this exact structure.
4. Return the digest and the IDs of every article you referenced.

Grouping rules:
- Merge articles only when they cover the same specific real-world event (for example,
  the same announcement, launch, or incident). Keep distinct developments as separate
  stories, even when they share a topic.
- For each story, choose the most complete or authoritative source as the primary source.

Start the digest with a short narrative intro paragraph (2-4 sentences). Do not mention
specific articles in the intro.

Then write one section per selected story using this template exactly:

**{primary_feed_name}**

## [{Primary Article Title}]({primary_url})

{2-3 sentence summary. Concise. No bullet points. When a story has multiple sources,
synthesise across them and note where they diverge.}

Also covered by: [{feed_name}]({url}) · [{feed_name}]({url})

[Comments]({comments_url})

Rules:
- The primary feed name must be bold text on its own line above the heading.
- The article title must be a Markdown link to the primary article URL.
- Include the "Also covered by" line only when the story has more than one source. List
  each secondary source as a Markdown link to its article, separated by " · ". Omit the
  line entirely for single-source stories.
- Omit the [Comments] link entirely if no comments_url is provided for the primary article.
- Summary: exactly 2-3 sentences, no lists, no sub-headings.
- Be concise. Prioritise stories with broad significance over niche topics.
- The returned article IDs must include every article you referenced in any story: the
  primary source and every "Also covered by" source.
"""
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `uv run pytest tests/ai/test_agent.py -k "clustering or also_covered_by or primary_source or referenced_id" -v`
Expected: PASS (all four).

- [ ] **Step 5: Run the full agent test file to catch regressions**

Run: `uv run pytest tests/ai/test_agent.py -v`
Expected: PASS. In particular `test_agent_initialized_with_correct_model`, `test_agent_uses_base_system_prompt_when_no_preferences`, and the `_build_system_prompt` tests still pass because they reference the `_SYSTEM_PROMPT` constant itself rather than its literal old text.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check src/minizen/ai/agent.py tests/ai/test_agent.py
uv run ruff format --check src/minizen/ai/agent.py tests/ai/test_agent.py
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat(ai): cluster same-event articles into one digest story

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Make `top_n` count stories

Reframe the user prompt and the `top_n` config description so the cap applies to deduplicated stories, and update the `run()` docstring accordingly.

**Files:**
- Modify: `src/minizen/ai/agent.py` (the `user_prompt` in `run()`, lines 195-198, and `run()`'s docstring at lines 170-182)
- Modify: `src/minizen/config/models.py` (`AIConfig.top_n` field description, lines 40-43)
- Test: `tests/ai/test_agent.py`

**Interfaces:**
- Consumes: `self._top_n` (already set in `__init__`), `_SYSTEM_PROMPT` from Task 1.
- Produces: `DigestAgent.run(*, articles: list[Article]) -> DigestResult` unchanged in signature; its user prompt now reads `"Please select the top {top_n} most important stories from the following and write a digest:"`. No change to `DigestResult` or to the pipeline.

- [ ] **Step 1: Write the failing test**

Add to `tests/ai/test_agent.py`:

```python
def test_run_prompts_for_top_n_stories(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=4)
    articles = [_make_article(article_id=1)]

    # act
    agent.run(articles=articles)

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "top 4 most important stories" in user_prompt
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/ai/test_agent.py::test_run_prompts_for_top_n_stories -v`
Expected: FAIL — current prompt says "most important articles", so the substring is absent.

- [ ] **Step 3: Update the user prompt and `run()` docstring**

In `src/minizen/ai/agent.py`, change the `user_prompt` assignment in `run()` (currently lines 195-198) from `"most important articles"` to `"most important stories"`:

```python
        user_prompt = (
            f"Please select the top {self._top_n} most important stories "  # noqa: S608
            f"from the following and write a digest:\n\n{articles_text}"
        )
```

Then update `run()`'s docstring summary line (currently line 171, `"""Select the top N articles and return a structured Markdown digest.`) to:

```python
        """Select the top N stories and return a structured Markdown digest.
```

and update its `Returns:` clause so "articles that were included" reads "articles that were referenced across the selected stories":

```python
        Returns:
            A ``DigestResult`` containing the Markdown text and the IDs of
            articles that were referenced across the selected stories.
```

- [ ] **Step 4: Update the `top_n` config description**

In `src/minizen/config/models.py`, change the `top_n` field description (lines 40-43) to:

```python
    top_n: int = Field(
        default=DEFAULT_TOP_N,
        description="Maximum number of stories (after deduplication) to include in the digest.",  # noqa: E501
    )
```

- [ ] **Step 5: Run the new test and the full suite**

Run: `uv run pytest`
Expected: PASS with 100% coverage. `test_run_passes_article_data_to_agent`, the comments-URL and category prompt tests, and all pipeline tests still pass because none of them assert on the word "articles" in the user prompt, and `articles_used`-driven `extra_articles` behavior is unchanged.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check src/minizen/ai/agent.py src/minizen/config/models.py tests/ai/test_agent.py
uv run ruff format --check src/minizen/ai/agent.py src/minizen/config/models.py tests/ai/test_agent.py
git add src/minizen/ai/agent.py src/minizen/config/models.py tests/ai/test_agent.py
git commit -m "feat(ai): count top_n as deduplicated stories

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notes on already-covered behavior (no task needed)

The spec's "plumbing test" — a secondary-source ID in `articles_used` being excluded from
`extra_articles` ("More to read") — is already exercised by
`tests/core/test_pipeline.py::test_pipeline_runs_full_flow`, which asserts
`render_email` is called with `extra_articles = [a for a in articles if a.id not in {1, 2}]`.
That is exactly the secondary-source-exclusion contract; adding a near-identical test would
duplicate it. The behavior that makes clustering safe (the LLM populating `articles_used`
with every referenced source) is asserted at the prompt level in Task 1, Step 1
(`test_system_prompt_requires_every_referenced_id`).

## Self-review

- **Spec coverage:** clustering behavior + render format + "Also covered by" template →
  Task 1. `top_n` counts stories (user prompt) → Task 2. `top_n` config description →
  Task 2, Step 4. `run()` docstring update → Task 2, Step 3. Email template "no structural
  change" → confirmed, no task. `articles_used` includes secondary sources / `extra_articles`
  diff → Task 1 prompt rule + existing pipeline test (Notes section). Error handling
  unchanged → no new failure path introduced. All spec sections map to a task or an
  explicit no-op.
- **Placeholder scan:** no TBD/TODO; every code and test block is complete literal content.
- **Type consistency:** `DigestResult(markdown=..., articles_used=...)`, `DigestAgent(model=..., top_n=...)`,
  and `agent.run(articles=...)` match the signatures in `src/minizen/ai/agent.py` and the
  existing test helpers `_make_article(...)` / `MockerFixture` usage.
