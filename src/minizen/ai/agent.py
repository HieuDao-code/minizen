import logging
from typing import cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent, AgentRunResult

from minizen.providers.rss.miniflux import Article

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a personal news curator. You receive a list of unread articles and must:
1. Select the top N most important and interesting articles.
2. Write a cohesive, well-structured Markdown digest covering those articles.
3. Return the digest and the IDs of the articles you selected.

Each article section must include a direct link to the original article URL.
Be concise. Prioritise articles with broad significance over niche topics.
"""


class DigestResult(BaseModel):
    """Structured output from the AI digest agent."""

    markdown: str = Field(description="Markdown digest text produced by the agent.")
    articles_used: list[int] = Field(
        description="IDs of the articles selected for the digest."
    )


class DigestAgent:
    """AI-powered agent that selects and summarises articles into a Markdown digest."""

    def __init__(self, *, model: str, top_n: int) -> None:
        """Initialise the agent with the given model and article limit.

        Args:
            model: pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).
            top_n: Maximum number of articles to include in the digest.
        """
        logger.debug("Initialising DigestAgent: model=%s, top_n=%d", model, top_n)
        self._top_n = top_n
        self._agent = Agent(
            model=model,
            output_type=DigestResult,
            system_prompt=_SYSTEM_PROMPT,
        )

    def run(self, *, articles: list[Article]) -> DigestResult:
        """Select the top N articles and return a structured Markdown digest.

        Args:
            articles: Full list of unread articles to choose from.

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
            f"Published: {a.published_at.isoformat()}\n\n"
            f"{a.content}"
            for a in articles
        )
        user_prompt = (
            f"Please select the top {self._top_n} most important articles "  # noqa: S608
            f"from the following and write a digest:\n\n{articles_text}"
        )
        result = self._agent.run_sync(user_prompt)
        return cast(AgentRunResult[DigestResult], result).output
