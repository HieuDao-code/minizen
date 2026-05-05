# Language Preservation & Word Limit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two configurable AI settings — `summary_language` (match or override article language) and `max_words_per_article` (hard-truncate content before it reaches the LLM) — defaulting to the existing behaviour so existing configs need no changes.

**Architecture:** Four sequential tasks. First wire the new fields into `AIConfig`, then add the truncation helper and update `DigestAgent` to use both settings, then forward the new fields through the pipeline and CLI, and finally update the configuration docs.

**Tech Stack:** `html.parser` (stdlib) for HTML stripping, `pydantic` for config models, `pydantic-ai` for the AI agent.

---

### Task 1: Add `summary_language` and `max_words_per_article` to `AIConfig`

Add two new optional fields to the `AIConfig` pydantic model. Defaults preserve existing behaviour: `"auto"` keeps the current language-neutral behaviour; `None` keeps the current no-truncation behaviour.

**Files:**
- Modify: `src/minizen/config/models.py`
- Modify: `tests/config/test_models.py`

- [ ] **Step 1: Write the failing tests**

Add the following four tests to `tests/config/test_models.py` (after the existing `test_ai_config_accepts_custom_values` test):

```python
def test_ai_config_default_summary_language() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.summary_language == "auto"


def test_ai_config_default_max_words_per_article() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.max_words_per_article is None


def test_ai_config_accepts_custom_summary_language() -> None:
    # act
    config = AIConfig(summary_language="English")

    # assert
    assert config.summary_language == "English"


def test_ai_config_accepts_custom_max_words_per_article() -> None:
    # act
    config = AIConfig(max_words_per_article=500)

    # assert
    assert config.max_words_per_article == 500
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/config/test_models.py -v
```

Expected: the four new tests FAIL with `TypeError: AIConfig() got an unexpected keyword argument`.

- [ ] **Step 3: Add the new fields to `AIConfig`**

In `src/minizen/config/models.py`, replace the `AIConfig` class with:

```python
class AIConfig(BaseModel):
    """AI model selection and digest size settings."""

    model: str = Field(
        default=DEFAULT_MODEL,
        description="pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).",  # noqa: E501
    )
    top_n: int = Field(
        default=DEFAULT_TOP_N,
        description="Maximum number of articles to include in the digest.",
    )
    summary_language: str = Field(
        default="auto",
        description=(
            'Language for article summaries. ``"auto"`` matches each article\'s '
            "language; any other value (e.g. ``\"English\"``) forces all summaries "
            "into that language."
        ),
    )
    max_words_per_article: int | None = Field(
        default=None,
        description=(
            "Maximum words of article content sent to the LLM per article. "
            "``None`` disables truncation."
        ),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/config/test_models.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/models.py tests/config/test_models.py
git commit -m "feat: add summary_language and max_words_per_article to AIConfig"
```

---

### Task 2: Add `_truncate_words` helper and update `DigestAgent`

Add a `_HTMLStripper`/`_truncate_words` pair to strip HTML and limit word count. Update `DigestAgent.__init__` to accept the two new settings and inject the language rule into the system prompt.

**Files:**
- Modify: `src/minizen/ai/agent.py`
- Modify: `tests/ai/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Replace `tests/ai/test_agent.py` with the following (the existing tests are preserved and updated; new tests are added at the end):

```python
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from minizen.ai.agent import DigestAgent, DigestResult, _truncate_words
from minizen.providers.rss.miniflux import Article

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_article(*, article_id: int = 1, comments_url: str | None = None) -> Article:
    return Article(
        id=article_id,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
        comments_url=comments_url,
    )


def test_run_returns_digest_result(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(
        markdown="# Digest\n\nSome news.",
        articles_used=[1],
    )
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=5)
    articles = [_make_article(article_id=1)]

    # act
    result = agent.run(articles=articles)

    # assert
    assert result.markdown == "# Digest\n\nSome news."
    assert result.articles_used == [1]
    mock_agent_cls.return_value.run_sync.assert_called_once_with(mocker.ANY)


def test_run_passes_article_data_to_agent(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[42])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=42)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Test Article" in user_prompt
    assert "Test Feed" in user_prompt
    assert "42" in user_prompt


def test_agent_initialized_with_correct_model(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(model="openai:gpt-4o", top_n=3)

    # assert
    mock_agent_cls.assert_called_once_with(
        model="openai:gpt-4o",
        output_type=DigestResult,
        system_prompt=mocker.ANY,
    )


def test_run_includes_comments_url_in_prompt_when_present(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [
        _make_article(
            article_id=1, comments_url="https://news.ycombinator.com/item?id=99"
        )
    ]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "https://news.ycombinator.com/item?id=99" in user_prompt


def test_run_omits_comments_url_in_prompt_when_none(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=1, comments_url=None)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Comments URL: None" not in user_prompt
    assert "ycombinator" not in user_prompt


# --- _truncate_words ---


def test_truncate_words_strips_html_tags() -> None:
    # act
    result = _truncate_words(html="<p>Hello world</p>", max_words=10)

    # assert
    assert "<p>" not in result
    assert "Hello" in result
    assert "world" in result


def test_truncate_words_truncates_at_exact_word_count() -> None:
    # arrange
    html = "<p>" + " ".join(f"word{i}" for i in range(100)) + "</p>"

    # act
    result = _truncate_words(html=html, max_words=5)

    # assert
    assert result.split() == ["word0", "word1", "word2", "word3", "word4"]


def test_truncate_words_preserves_all_words_when_under_limit() -> None:
    # act
    result = _truncate_words(html="<p>one two three</p>", max_words=10)

    # assert
    assert result.split() == ["one", "two", "three"]


# --- language rule in system prompt ---


def test_auto_language_rule_appears_in_system_prompt(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3, summary_language="auto")

    # assert
    system_prompt: str = mock_agent_cls.call_args.kwargs["system_prompt"]
    assert "same language the article is written in" in system_prompt


def test_specific_language_rule_appears_in_system_prompt(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-4-6", top_n=3, summary_language="English"
    )

    # assert
    system_prompt: str = mock_agent_cls.call_args.kwargs["system_prompt"]
    assert "Write all summaries in English" in system_prompt


# --- max_words_per_article wiring ---


def test_run_truncates_content_at_max_words(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    long_content = "<p>" + " ".join(f"word{i}" for i in range(200)) + "</p>"
    article = Article(
        id=1,
        title="Test",
        url="https://example.com",
        content=long_content,
        feed_name="Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
    )
    agent = DigestAgent(
        model="anthropic:claude-sonnet-4-6", top_n=3, max_words_per_article=50
    )

    # act
    agent.run(articles=[article])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "word49" in user_prompt
    assert "word50" not in user_prompt


def test_run_passes_full_content_when_max_words_is_none(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    long_content = "<p>" + " ".join(f"word{i}" for i in range(200)) + "</p>"
    article = Article(
        id=1,
        title="Test",
        url="https://example.com",
        content=long_content,
        feed_name="Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
    )
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)

    # act
    agent.run(articles=[article])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "word199" in user_prompt
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: the new `_truncate_words`, language rule, and `max_words_per_article` tests FAIL — the function and constructor params don't exist yet.

- [ ] **Step 3: Implement the changes**

Replace `src/minizen/ai/agent.py` with:

```python
"""AI agent for curating and summarising RSS articles into a Markdown digest."""

import logging
from html.parser import HTMLParser
from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent, AgentRunResult

if TYPE_CHECKING:
    from minizen.providers.rss.miniflux import Article

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a personal news curator. You receive a list of unread articles and must:
1. Select the top N most important and interesting articles.
2. Write a cohesive Markdown digest following this exact structure.
3. Return the digest and the IDs of the articles you selected.

Start the digest with a short narrative intro paragraph (2-4 sentences). Do not mention
specific articles in the intro.

Then write one section per selected article using this template exactly:

**{feed_name}**

## [{Article Title}]({url})

{2-3 sentence summary. Concise. No bullet points.}

[Comments]({comments_url})

Rules:
- The feed name must be bold text on its own line above the heading.
- The article title must be a Markdown link to the article URL.
- Omit the [Comments] link entirely if no comments_url is provided for that article.
- Summary: exactly 2-3 sentences, no lists, no sub-headings.
- Be concise. Prioritise articles with broad significance over niche topics.
"""


class _HTMLStripper(HTMLParser):
    """HTMLParser subclass that accumulates text nodes, discarding tags."""

    def __init__(self) -> None:
        """Initialise with an empty text buffer."""
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        """Collect a text node.

        Args:
            data: Raw text content between HTML tags.
        """
        self._parts.append(data)

    @property
    def text(self) -> str:
        """All collected text nodes joined by spaces.

        Returns:
            Plain text with all HTML tags removed.
        """
        return " ".join(self._parts)


def _truncate_words(html: str, max_words: int) -> str:
    """Strip HTML tags from *html* and return at most *max_words* words.

    Args:
        html: Raw HTML string (article content from Miniflux).
        max_words: Maximum number of whitespace-delimited words to return.

    Returns:
        Plain text with HTML stripped, truncated to *max_words* words.
    """
    parser = _HTMLStripper()
    parser.feed(html)
    words = parser.text.split()
    return " ".join(words[:max_words])


class DigestResult(BaseModel):
    """Structured output from the AI digest agent."""

    markdown: str = Field(description="Markdown digest text produced by the agent.")
    articles_used: list[int] = Field(
        description="IDs of the articles selected for the digest."
    )


class DigestAgent:
    """AI-powered agent that selects and summarises articles into a Markdown digest."""

    def __init__(
        self,
        *,
        model: str,
        top_n: int,
        summary_language: str = "auto",
        max_words_per_article: int | None = None,
    ) -> None:
        """Initialise the agent with the given model and digest settings.

        Args:
            model: pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).
            top_n: Maximum number of articles to include in the digest.
            summary_language: Language for summaries. ``"auto"`` matches each
                article's language; any other value (e.g. ``"English"``) forces
                all summaries into that language.
            max_words_per_article: Maximum words of article content sent to the
                LLM per article. ``None`` disables truncation.
        """
        logger.debug(
            "Initialising DigestAgent: model=%s, top_n=%d, summary_language=%s, max_words=%s",
            model,
            top_n,
            summary_language,
            max_words_per_article,
        )
        self._top_n = top_n
        self._max_words_per_article = max_words_per_article
        if summary_language == "auto":
            language_rule = (
                "Write each article's summary in the same language "
                "the article is written in."
            )
        else:
            language_rule = f"Write all summaries in {summary_language}."
        system_prompt = _SYSTEM_PROMPT + f"- {language_rule}\n"
        self._agent = Agent(
            model=model,
            output_type=DigestResult,
            system_prompt=system_prompt,
        )

    def run(self, *, articles: list[Article]) -> DigestResult:
        """Select the top N articles and return a structured Markdown digest.

        Args:
            articles: Full list of articles to choose from.

        Returns:
            A ``DigestResult`` containing the Markdown text and the IDs of
            articles that were included.
        """
        logger.info("Running AI agent on %d article(s)", len(articles))
        articles_text = "\n\n---\n\n".join(
            f"ID: {a.id}\n"
            f"Feed: {a.feed_name}\n"
            f"Title: {a.title}\n"
            f"URL: {a.url}\n"
            f"Published: {a.published_at.isoformat()}\n"
            + (f"Comments URL: {a.comments_url}\n" if a.comments_url else "")
            + "\n"
            + (
                _truncate_words(a.content, self._max_words_per_article)
                if self._max_words_per_article
                else a.content
            )
            for a in articles
        )
        user_prompt = (
            f"Please select the top {self._top_n} most important articles "  # noqa: S608
            f"from the following and write a digest:\n\n{articles_text}"
        )
        result = self._agent.run_sync(user_prompt)
        return cast("AgentRunResult[DigestResult]", result).output
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat: add language rule and word-limit truncation to DigestAgent"
```

---

### Task 3: Wire new fields through pipeline and CLI

Forward `summary_language` and `max_words_per_article` from `settings.ai` to `DigestAgent` in the pipeline and both CLI commands. Update the tests to verify the new constructor arguments are passed.

**Files:**
- Modify: `src/minizen/core/pipeline.py`
- Modify: `src/minizen/cli/commands/digest.py`
- Modify: `tests/core/test_pipeline.py`
- Modify: `tests/cli/commands/test_digest.py`

- [ ] **Step 1: Update the pipeline test**

In `tests/core/test_pipeline.py`, find `test_pipeline_runs_full_flow`. Change the line:

```python
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
```

to:

```python
    mock_agent_cls = mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
```

Then add the following assertion at the end of that test's `# assert` block (after the `mock_email.send` assertion):

```python
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=2,
        summary_language="auto",
        max_words_per_article=None,
    )
```

- [ ] **Step 2: Update the CLI tests**

In `tests/cli/commands/test_digest.py`, update `_make_settings_mock()` to include the two new fields:

```python
def _make_settings_mock() -> MagicMock:
    mock = MagicMock()
    mock.ai.model = "anthropic:claude-sonnet-4-6"
    mock.ai.top_n = 5
    mock.ai.summary_language = "auto"
    mock.ai.max_words_per_article = None
    return mock
```

In `test_digest_preview_prints_markdown`, change:

```python
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
```

to:

```python
    mock_agent_cls = mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
```

And add at the end of the `# assert` block:

```python
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        summary_language="auto",
        max_words_per_article=None,
    )
```

In `test_digest_send_test_sends_email`, change:

```python
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
```

to:

```python
    mock_agent_cls = mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
```

And add at the end of the `# assert` block:

```python
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        summary_language="auto",
        max_words_per_article=None,
    )
```

- [ ] **Step 3: Run updated tests to verify they fail**

```bash
uv run pytest tests/core/test_pipeline.py::test_pipeline_runs_full_flow tests/cli/commands/test_digest.py::test_digest_preview_prints_markdown tests/cli/commands/test_digest.py::test_digest_send_test_sends_email -v
```

Expected: all three tests FAIL — `DigestAgent` is called without the new kwargs.

- [ ] **Step 4: Update `pipeline.py`**

In `src/minizen/core/pipeline.py`, replace the line:

```python
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
```

with:

```python
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        summary_language=settings.ai.summary_language,
        max_words_per_article=settings.ai.max_words_per_article,
    )
```

- [ ] **Step 5: Update `digest.py`**

In `src/minizen/cli/commands/digest.py`, there are two `DigestAgent(...)` calls — one in `preview` and one in `send_test`. Replace both occurrences of:

```python
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
```

with:

```python
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        summary_language=settings.ai.summary_language,
        max_words_per_article=settings.ai.max_words_per_article,
    )
```

- [ ] **Step 6: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS, coverage 100%.

- [ ] **Step 7: Commit**

```bash
git add src/minizen/core/pipeline.py src/minizen/cli/commands/digest.py tests/core/test_pipeline.py tests/cli/commands/test_digest.py
git commit -m "feat: wire summary_language and max_words_per_article through pipeline and CLI"
```

---

### Task 4: Update configuration docs

Add the two new fields to the `[ai]` section of `docs/configuration.md`.

**Files:**
- Modify: `docs/configuration.md`

- [ ] **Step 1: Update the `[ai]` table**

In `docs/configuration.md`, replace the `[ai]` section table:

```markdown
| Key     | Type    | Default                        | Description                               |
| ------- | ------- | ------------------------------ | ----------------------------------------- |
| `model` | string  | `"anthropic:claude-haiku-4-5"` | pydantic-ai model identifier              |
| `top_n` | integer | `5`                            | Number of articles selected for full AI summaries; remaining recent articles appear as a "More to read" link list |
```

with:

```markdown
| Key                      | Type             | Default                        | Description |
| ------------------------ | ---------------- | ------------------------------ | ----------- |
| `model`                  | string           | `"anthropic:claude-haiku-4-5"` | pydantic-ai model identifier |
| `top_n`                  | integer          | `5`                            | Number of articles selected for full AI summaries; remaining recent articles appear as a "More to read" link list |
| `summary_language`       | string           | `"auto"`                       | Language for summaries. `"auto"` matches each article's original language; any other value (e.g. `"English"`) forces all summaries into that language. |
| `max_words_per_article`  | integer or unset | unset                          | Maximum words of article content sent to the LLM. Unset means no limit. Set to e.g. `500` to reduce token usage. |
```

- [ ] **Step 2: Update the example TOML block**

In the manual setup section, replace the `[ai]` block inside the TOML template:

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
```

with:

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
# summary_language = "English"   # default: "auto" (match article language)
# max_words_per_article = 500    # default: unset (no truncation)
```

- [ ] **Step 3: Commit**

```bash
git add docs/configuration.md
git commit -m "docs: add summary_language and max_words_per_article to configuration reference"
```
