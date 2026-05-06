"""Miniflux RSS provider for fetching articles published in the last 24 hours."""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import miniflux
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from minizen.config.models import MinifluxConfig

logger = logging.getLogger(__name__)

_LOOKBACK_HOURS = 24


class Article(BaseModel):
    """A single RSS article fetched from Miniflux."""

    id: int = Field(description="Miniflux entry ID.")
    title: str = Field(description="Article title.")
    url: str = Field(description="Canonical URL of the article.")
    content: str = Field(description="Full HTML or text content of the article.")
    feed_name: str = Field(description="Name of the feed the article belongs to.")
    published_at: datetime = Field(description="Publication timestamp (UTC-aware).")
    comments_url: str | None = Field(
        default=None,
        description="URL of the article's comments section, if available.",
    )


class MinifluxProvider:
    """RSS provider that reads articles via the Miniflux API."""

    def __init__(self, *, config: MinifluxConfig) -> None:
        """Initialise the Miniflux client from the given configuration.

        Args:
            config: Miniflux connection settings (URL and API key).
        """
        self._client = miniflux.Client(
            base_url=config.url,
            api_key=config.api_key,
        )

    def fetch_recent(self) -> list[Article]:
        """Return all articles from the last 24 hours, read or unread.

        Returns:
            A list of ``Article`` objects, one per entry in the lookback window.

        Raises:
            miniflux.AccessUnauthorized: If the API key is invalid or missing.
            miniflux.ClientError: If the Miniflux API returns any other error response,
                including HTTP 429 rate-limit responses.
            OSError: If a network error occurs while contacting Miniflux.
        """
        cutoff = datetime.now(tz=UTC) - timedelta(hours=_LOOKBACK_HOURS)
        after_ts = int(cutoff.timestamp())
        try:
            response = self._client.get_entries(published_after=after_ts)
        except miniflux.AccessUnauthorized:
            logger.error("Miniflux authentication failed: invalid API key")
            raise
        except miniflux.ClientError as exc:
            if exc.status_code == 429:  # noqa: PLR2004
                logger.error("Miniflux API rate limit exceeded (HTTP 429)")
            else:
                logger.error("Miniflux API error (HTTP %d): %s", exc.status_code, exc)
            raise
        except OSError as exc:
            logger.error("Network error connecting to Miniflux: %s", exc)
            raise
        entries = response.get("entries") or []
        logger.debug(
            "Fetched %d entries from the last %dh", len(entries), _LOOKBACK_HOURS
        )
        return [
            Article(
                id=entry["id"],
                title=entry["title"],
                url=entry["url"],
                content=entry["content"],
                feed_name=entry["feed"]["title"],
                published_at=datetime.fromisoformat(entry["published_at"]),
                comments_url=entry.get("comments_url") or None,
            )
            for entry in entries
        ]
