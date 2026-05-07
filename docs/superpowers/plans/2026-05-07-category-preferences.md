# Category Preferences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `preferred_categories` field to `[ai]` config so the AI prioritises articles from specific Miniflux categories when building the digest.

**Architecture:** `preferred_categories` lives in `AIConfig` alongside `interests`/`avoid`. The Miniflux entry response already embeds `feed.category.title`, so `Article` gains a `category` field with no extra API calls. `_build_system_prompt` appends a preference line when the list is non-empty, and `DigestAgent.run` includes a `Category:` line in each article block so the AI can match it.

**Tech Stack:** Python, Pydantic, pydantic-ai, miniflux Python client, pytest, pytest-mock

---

## File Map

| File | Change |
|------|--------|
| `src/minizen/config/models.py` | Add `preferred_categories` to `AIConfig` |
| `src/minizen/providers/rss/miniflux.py` | Add `category` to `Article`, extract from entry |
| `src/minizen/ai/agent.py` | Add `preferred_categories` to `_build_system_prompt` and `DigestAgent.__init__`; add `Category:` line in `run()` |
| `src/minizen/core/pipeline.py` | Pass `preferred_categories` to `DigestAgent` |
| `docs/configuration.md` | Document `preferred_categories` |
| `tests/config/test_models.py` | Tests for `preferred_categories` in `AIConfig` |
| `tests/providers/rss/test_miniflux.py` | Tests for `category` extraction and fallback |
| `tests/ai/test_agent.py` | Tests for `_build_system_prompt` and `DigestAgent` with `preferred_categories`; `Category:` in prompt |
| `tests/core/test_pipeline.py` | Update existing assertions + test for `preferred_categories` threading |

---

### Task 1: `preferred_categories` in `AIConfig`

**Files:**
- Modify: `src/minizen/config/models.py`
- Modify: `tests/config/test_models.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/config/test_models.py`:

```python
def test_ai_config_defaults_preferred_categories_to_empty_list() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.preferred_categories == []


def test_ai_config_accepts_preferred_categories() -> None:
    # act
    config = AIConfig(preferred_categories=["Tech", "Science"])

    # assert
    assert config.preferred_categories == ["Tech", "Science"]
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/config/test_models.py::test_ai_config_defaults_preferred_categories_to_empty_list tests/config/test_models.py::test_ai_config_accepts_preferred_categories -v
```

Expected: FAIL with `ValidationError` or `TypeError` (field does not exist).

- [ ] **Step 3: Add `preferred_categories` to `AIConfig`**

In `src/minizen/config/models.py`, add after the `avoid` field:

```python
preferred_categories: list[str] = Field(
    default_factory=list,
    description="Miniflux category names to prioritise when selecting articles.",
)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/config/test_models.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/models.py tests/config/test_models.py
git commit -m "feat: add preferred_categories to AIConfig"
```

---

### Task 2: `category` field on `Article`

**Files:**
- Modify: `src/minizen/providers/rss/miniflux.py`
- Modify: `tests/providers/rss/test_miniflux.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/providers/rss/test_miniflux.py`:

```python
@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_extracts_category_from_entry(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 1,
                "title": "Test",
                "url": "https://example.com",
                "content": "<p>Body</p>",
                "feed": {"title": "Hacker News", "category": {"title": "Tech"}},
                "published_at": "2026-05-04T08:00:00Z",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles[0].category == "Tech"


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_defaults_category_to_empty_string_when_absent(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 1,
                "title": "Test",
                "url": "https://example.com",
                "content": "<p>Body</p>",
                "feed": {"title": "Hacker News"},
                "published_at": "2026-05-04T08:00:00Z",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles[0].category == ""
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/providers/rss/test_miniflux.py::test_fetch_recent_extracts_category_from_entry tests/providers/rss/test_miniflux.py::test_fetch_recent_defaults_category_to_empty_string_when_absent -v
```

Expected: FAIL — `Article` has no `category` field.

- [ ] **Step 3: Add `category` to `Article` and extract it in `fetch_recent`**

In `src/minizen/providers/rss/miniflux.py`, add after `feed_name`:

```python
category: str = Field(
    default="",
    description="Miniflux category the feed belongs to, or empty string if uncategorised.",
)
```

In `fetch_recent`, update the `Article(...)` constructor call to add:

```python
category=entry["feed"].get("category", {}).get("title", ""),
```

The full updated `Article(...)` block becomes:

```python
Article(
    id=entry["id"],
    title=entry["title"],
    url=entry["url"],
    content=entry["content"],
    feed_name=entry["feed"]["title"],
    category=entry["feed"].get("category", {}).get("title", ""),
    published_at=datetime.fromisoformat(entry["published_at"]),
    comments_url=entry.get("comments_url") or None,
)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/providers/rss/test_miniflux.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/providers/rss/miniflux.py tests/providers/rss/test_miniflux.py
git commit -m "feat: add category field to Article extracted from Miniflux entry"
```

---

### Task 3: `_build_system_prompt` and `DigestAgent` with `preferred_categories`

**Files:**
- Modify: `src/minizen/ai/agent.py`
- Modify: `tests/ai/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Update the import line at the top of `tests/ai/test_agent.py` to include `_build_system_prompt`:

```python
from minizen.ai.agent import _SYSTEM_PROMPT, _build_system_prompt, DigestAgent, DigestResult, _truncate_words
```

Add these tests:

```python
def test_build_system_prompt_includes_preferred_categories_when_set() -> None:
    # act
    result = _build_system_prompt(
        interests=[],
        avoid=[],
        preferred_categories=["Tech", "Science"],
    )

    # assert
    assert (
        "Prefer articles from these Miniflux categories (in order of preference): Tech, Science"
        in result
    )


def test_build_system_prompt_omits_preferred_categories_line_when_empty() -> None:
    # act
    result = _build_system_prompt(interests=[], avoid=[], preferred_categories=[])

    # assert
    assert result == _SYSTEM_PROMPT


def test_agent_initialized_with_preference_block_when_preferred_categories_set(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        preferred_categories=["Tech", "Science"],
    )

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert (
        "Prefer articles from these Miniflux categories (in order of preference): Tech, Science"
        in call_kwargs["system_prompt"]
    )
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/ai/test_agent.py::test_build_system_prompt_includes_preferred_categories_when_set tests/ai/test_agent.py::test_build_system_prompt_omits_preferred_categories_line_when_empty tests/ai/test_agent.py::test_agent_initialized_with_preference_block_when_preferred_categories_set -v
```

Expected: FAIL — `_build_system_prompt` not exported or missing `preferred_categories` parameter.

- [ ] **Step 3: Update `_build_system_prompt` and `DigestAgent.__init__`**

Replace the `_build_system_prompt` function in `src/minizen/ai/agent.py`:

```python
def _build_system_prompt(
    *, interests: list[str], avoid: list[str], preferred_categories: list[str]
) -> str:
    """Build the system prompt, appending a user-preference block when non-empty.

    Args:
        interests: Topics the user wants to prioritise.
        avoid: Topics the user wants to exclude.
        preferred_categories: Miniflux category names to prefer when selecting articles.

    Returns:
        The base system prompt unchanged when all lists are empty, or with a
        ``User preferences:`` block appended when at least one list is non-empty.
    """
    if not interests and not avoid and not preferred_categories:
        return _SYSTEM_PROMPT
    lines = ["User preferences:"]
    if interests:
        lines.append(f"- Prioritise articles about: {', '.join(interests)}")
    if avoid:
        lines.append(f"- Avoid articles about: {', '.join(avoid)}")
    if preferred_categories:
        lines.append(
            f"- Prefer articles from these Miniflux categories"
            f" (in order of preference): {', '.join(preferred_categories)}"
        )
    return _SYSTEM_PROMPT + "\n" + "\n".join(lines) + "\n"
```

Replace the `DigestAgent.__init__` signature and body in `src/minizen/ai/agent.py`:

```python
def __init__(
    self,
    *,
    model: str,
    top_n: int,
    max_words_per_article: int = 500,
    interests: list[str] | None = None,
    avoid: list[str] | None = None,
    preferred_categories: list[str] | None = None,
) -> None:
    """Initialise the agent with the given model and digest settings.

    Args:
        model: pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).
        top_n: Maximum number of articles to include in the digest.
        max_words_per_article: Maximum words of article content sent to the
            LLM per article.
        interests: Topics to prioritise when selecting articles.
        avoid: Topics to exclude when selecting articles.
        preferred_categories: Miniflux category names to prefer when selecting articles.
    """
    logger.debug(
        "Initialising DigestAgent: model=%s, top_n=%d, max_words=%d",
        model,
        top_n,
        max_words_per_article,
    )
    self._top_n = top_n
    self._max_words_per_article = max_words_per_article
    system_prompt = _build_system_prompt(
        interests=interests or [],
        avoid=avoid or [],
        preferred_categories=preferred_categories or [],
    )
    self._agent = Agent(
        model=model,
        output_type=DigestResult,
        system_prompt=system_prompt,
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat: add preferred_categories to _build_system_prompt and DigestAgent"
```

---

### Task 4: Include `Category:` in article text sent to AI

**Files:**
- Modify: `src/minizen/ai/agent.py`
- Modify: `tests/ai/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/ai/test_agent.py`:

```python
def test_run_includes_category_in_prompt_when_present(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    article = Article(
        id=1,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        category="Tech",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
    )

    # act
    agent.run(articles=[article])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "Category: Tech" in user_prompt


def test_run_omits_category_in_prompt_when_empty(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)

    # act
    agent.run(articles=[_make_article(article_id=1)])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "Category:" not in user_prompt
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/ai/test_agent.py::test_run_includes_category_in_prompt_when_present tests/ai/test_agent.py::test_run_omits_category_in_prompt_when_empty -v
```

Expected: FAIL — `Category:` line is not in the prompt yet.

- [ ] **Step 3: Add `Category:` line to article text in `DigestAgent.run`**

In `src/minizen/ai/agent.py`, replace the `articles_text` assignment inside `run`:

```python
articles_text = "\n\n---\n\n".join(
    f"ID: {a.id}\n"
    f"Feed: {a.feed_name}\n"
    + (f"Category: {a.category}\n" if a.category else "")
    + f"Title: {a.title}\n"
    f"URL: {a.url}\n"
    f"Published: {a.published_at.isoformat()}\n"
    + (f"Comments URL: {a.comments_url}\n" if a.comments_url else "")
    + f"\n{_truncate_words(a.content, self._max_words_per_article)}"
    for a in articles
)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat: include article category in AI prompt when present"
```

---

### Task 5: Thread `preferred_categories` through the pipeline

**Files:**
- Modify: `src/minizen/core/pipeline.py`
- Modify: `tests/core/test_pipeline.py`

- [ ] **Step 1: Write the failing test and update the existing assertions**

In `tests/core/test_pipeline.py`:

Update `_make_settings` to accept `preferred_categories`:

```python
def _make_settings(
    *,
    interests: list[str] | None = None,
    avoid: list[str] | None = None,
    preferred_categories: list[str] | None = None,
) -> Settings:
    return Settings(
        miniflux=MinifluxConfig(url="https://rss.example.com", api_key="key"),
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="from@example.com",
            to_addr="to@example.com",
            username="user",
            password="pass",
        ),
        ai=AIConfig(
            model="anthropic:claude-sonnet-4-6",
            top_n=2,
            interests=interests or [],
            avoid=avoid or [],
            preferred_categories=preferred_categories or [],
        ),
    )
```

In `test_pipeline_runs_full_flow`, update the assertion:

```python
mock_agent_cls.assert_called_once_with(
    model="anthropic:claude-sonnet-4-6",
    top_n=2,
    max_words_per_article=500,
    interests=[],
    avoid=[],
    preferred_categories=[],
)
```

In `test_pipeline_passes_interests_and_avoid_to_agent`, update the assertion:

```python
mock_agent_cls.assert_called_once_with(
    model="anthropic:claude-sonnet-4-6",
    top_n=2,
    max_words_per_article=500,
    interests=["Rust", "AI"],
    avoid=["sports"],
    preferred_categories=[],
)
```

Add the new test:

```python
@freeze_time("2026-04-29")
def test_pipeline_passes_preferred_categories_to_agent(
    mocker: MockerFixture,
) -> None:
    # arrange
    articles = [_make_article(1)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_email = MagicMock()
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mock_agent_cls = mocker.patch(
        "minizen.core.pipeline.DigestAgent", return_value=mock_agent
    )
    mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    settings = _make_settings(preferred_categories=["Tech", "Science"])

    # act
    run_pipeline(settings=settings)

    # assert
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=2,
        max_words_per_article=500,
        interests=[],
        avoid=[],
        preferred_categories=["Tech", "Science"],
    )
```

- [ ] **Step 2: Run tests to confirm the new test fails and the updated assertions fail**

```bash
uv run pytest tests/core/test_pipeline.py -v
```

Expected: `test_pipeline_passes_preferred_categories_to_agent` FAIL, `test_pipeline_runs_full_flow` FAIL, `test_pipeline_passes_interests_and_avoid_to_agent` FAIL (missing `preferred_categories` kwarg).

- [ ] **Step 3: Update `run_pipeline` to pass `preferred_categories`**

In `src/minizen/core/pipeline.py`, update the `DigestAgent(...)` call:

```python
agent = DigestAgent(
    model=settings.ai.model,
    top_n=settings.ai.top_n,
    max_words_per_article=settings.ai.max_words_per_article,
    interests=settings.ai.interests,
    avoid=settings.ai.avoid,
    preferred_categories=settings.ai.preferred_categories,
)
```

- [ ] **Step 4: Run the full test suite**

```bash
uv run pytest -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/core/pipeline.py tests/core/test_pipeline.py
git commit -m "feat: thread preferred_categories from settings to DigestAgent"
```

---

### Task 6: Documentation

**Files:**
- Modify: `docs/configuration.md`

- [ ] **Step 1: Add `preferred_categories` to the `[ai]` table**

In `docs/configuration.md`, add a row to the `### [ai] section` table after the `avoid` row:

```markdown
| `preferred_categories` | list of strings | `[]` | Miniflux category names for the AI to prefer when selecting articles (e.g. `["Tech", "Science"]`). Listed in order of preference. Omit or leave empty for no preference. |
```

- [ ] **Step 2: Add a "Category preferences" subsection**

After the closing paragraph of the "Interest profile" subsection, add:

```markdown
#### Category preferences

Use `preferred_categories` to steer the AI toward articles from specific Miniflux categories.
Categories are matched by their exact name in Miniflux (case-sensitive).

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
preferred_categories = ["Tech", "Science"]
```

The AI will favour articles from the listed categories when choosing the top N, treating earlier
entries as higher priority. This works alongside `interests` and `avoid` — all three fields
influence the same selection step. Unknown category names are silently ignored.
```

- [ ] **Step 3: Update the config template in the manual setup section**

In the "Create the config file" code block under "Manual setup", add a commented-out line after the `avoid` example:

```toml
# preferred_categories = ["Tech", "Science"]            # optional
```

- [ ] **Step 4: Commit**

```bash
git add docs/configuration.md
git commit -m "docs: document preferred_categories in configuration reference"
```
