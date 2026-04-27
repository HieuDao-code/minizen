"""Miniflux RSS provider for fetching and marking articles via the Miniflux API."""

import logging
from datetime import datetime

import miniflux
from pydantic import BaseModel, Field

from minizen.config.models import MinifluxConfig

logger = logging.getLogger(__name__)


class Article(BaseModel):
    """A single RSS article fetched from Miniflux."""

    id: int = Field(description="Miniflux entry ID.")
    title: str = Field(description="Article title.")
    url: str = Field(description="Canonical URL of the article.")
    content: str = Field(description="Full HTML or text content of the article.")
    feed_name: str = Field(description="Name of the feed the article belongs to.")
    published_at: datetime = Field(description="Publication timestamp (UTC-aware).")


class MinifluxProvider:
    """RSS provider that reads and marks articles via the Miniflux API."""

    def __init__(self, *, config: MinifluxConfig) -> None:
        """Initialise the Miniflux client from the given configuration.

        Args:
            config: Miniflux connection settings (URL and API key).
        """
        self._client = miniflux.Client(
            base_url=config.url,
            api_key=config.api_key,
        )

    def fetch_unread(self) -> list[Article]:
        """Return all unread articles from the Miniflux instance.

        Returns:
            A list of ``Article`` objects, one per unread entry.
        """
        response = self._client.get_entries(status=["unread"])
        entries = response["entries"]
        logger.debug("Fetched %d unread entries from Miniflux", len(entries))
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
            for entry in entries
        ]

    def mark_as_read(self, *, article_ids: list[int]) -> None:
        """Mark the given article IDs as read in Miniflux.

        Args:
            article_ids: IDs of articles to mark as read.
        """
        logger.debug("Marking articles as read: ids=%s", article_ids)
        self._client.update_entries(entry_ids=article_ids, status="read")
