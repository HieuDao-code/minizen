from datetime import datetime

import miniflux
from pydantic import BaseModel

from minizen.config.models import MinifluxConfig


class Article(BaseModel):
    id: int
    title: str
    url: str
    content: str
    feed_name: str
    published_at: datetime


class MinifluxProvider:
    def __init__(self, *, config: MinifluxConfig) -> None:
        self._client = miniflux.Client(
            base_url=config.url,
            api_key=config.api_key,
        )

    def fetch_unread(self) -> list[Article]:
        response = self._client.get_entries(status=["unread"])
        return [
            Article(
                id=entry["id"],
                title=entry["title"],
                url=entry["url"],
                content=entry["content"],
                feed_name=entry["feed"]["title"],
                published_at=datetime.fromisoformat(
                    entry["published_at"].replace("Z", "+00:00")
                ),
            )
            for entry in response["entries"]
        ]

    def mark_as_read(self, *, article_ids: list[int]) -> None:
        self._client.update_entries(entry_ids=article_ids, status="read")
