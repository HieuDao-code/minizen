"""Miniflux RSS provider for fetching articles published in the last 24 hours."""

import http
import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import miniflux
from pydantic import BaseModel, Field

from minizen.exceptions import MinifluxError
from minizen.retry import retry_transient

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


def is_transient_miniflux(exc: BaseException) -> bool:
    """Return True if exc is a transient Miniflux error that warrants a retry.

    Args:
        exc: The exception to classify.

    Returns:
        True for ``OSError`` and ``miniflux.ClientError`` with a 5xx status code;
        False for 4xx client errors and all other exception types.
    """
    if isinstance(exc, OSError):
        return True
    if isinstance(exc, miniflux.ClientError) and isinstance(exc.status_code, int):
        return exc.status_code >= http.HTTPStatus.INTERNAL_SERVER_ERROR
    return False


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
            MinifluxError: If the Miniflux API call fails after all retries.
        """
        cutoff = datetime.now(tz=UTC) - timedelta(hours=_LOOKBACK_HOURS)
        after_ts = int(cutoff.timestamp())
        try:
            response = self._get_entries(after_ts=after_ts)
        except (miniflux.ClientError, OSError) as exc:
            msg = f"Miniflux API error: {exc}"
            raise MinifluxError(msg) from exc
        entries = response["entries"]
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

    @retry_transient(is_transient_miniflux)
    def _get_entries(self, *, after_ts: int) -> dict:
        """Fetch raw entries from Miniflux, retrying on transient errors.

        Args:
            after_ts: Unix timestamp; only entries published after this are returned.

        Returns:
            Raw Miniflux API response dict.

        Raises:
            miniflux.ClientError: On API errors (retried if 5xx, re-raised if 4xx).
            OSError: On network-level failures (always retried).
        """
        return self._client.get_entries(published_after=after_ts)
