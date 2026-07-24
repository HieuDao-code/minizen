"""AI agent for curating and summarising RSS articles into a Markdown digest."""

import logging
from html.parser import HTMLParser
from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.exceptions import AgentRunError

from minizen.exceptions import AIError

if TYPE_CHECKING:
    from minizen.providers.rss.miniflux import Article

logger = logging.getLogger(__name__)

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
- For each story, choose the most complete or authoritative source as the
  primary source.

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
- Omit the [Comments] link entirely if no comments_url is provided for the
  primary article.
- Summary: exactly 2-3 sentences, no lists, no sub-headings.
- Be concise. Prioritise stories with broad significance over niche topics.
- The returned article IDs must include every article you referenced in any story: the
  primary source and every "Also covered by" source.
"""


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
            preferred_categories: Miniflux category names to prefer when selecting
                articles.
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

    def run(self, *, articles: list[Article]) -> DigestResult:
        """Select the top N stories and return a structured Markdown digest.

        Args:
            articles: Full list of articles to choose from.

        Returns:
            A ``DigestResult`` containing the Markdown text and the IDs of
            articles that were referenced across the selected stories.

        Raises:
            AIError: If the AI model call fails.
        """
        logger.info("Running AI agent on %d article(s)", len(articles))
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
        user_prompt = (
            f"Please select the top {self._top_n} most important stories "  # noqa: S608
            f"from the following and write a digest:\n\n{articles_text}"
        )
        try:
            result = self._agent.run_sync(user_prompt)
        except AgentRunError as exc:
            msg = f"AI model error: {exc}"
            raise AIError(msg) from exc
        return cast("AgentRunResult[DigestResult]", result).output
