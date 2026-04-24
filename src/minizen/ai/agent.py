from typing import cast

from pydantic import BaseModel
from pydantic_ai import Agent, AgentRunResult

from minizen.providers.rss.miniflux import Article

_SYSTEM_PROMPT = """\
You are a personal news curator. You receive a list of unread articles and must:
1. Select the top N most important and interesting articles.
2. Write a cohesive, well-structured Markdown digest covering those articles.
3. Return the digest and the IDs of the articles you selected.

Be concise. Prioritise articles with broad significance over niche topics.
"""


class DigestResult(BaseModel):
    markdown: str
    articles_used: list[int]


class DigestAgent:
    def __init__(self, *, model: str, top_n: int) -> None:
        self._top_n = top_n
        self._agent = Agent(
            model=model,
            output_type=DigestResult,
            system_prompt=_SYSTEM_PROMPT,
        )

    def run(self, *, articles: list[Article]) -> DigestResult:
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
