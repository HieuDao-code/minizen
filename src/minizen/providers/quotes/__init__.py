"""Favourite quote provider for the digest's closing quote."""

import logging
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from minizen.providers.quotes.obsidian import ObsidianQuoteProvider, Quote
from minizen.providers.quotes.selection import pick_daily

if TYPE_CHECKING:
    from minizen.config.models import QuotesConfig

__all__ = ["Quote", "load_daily_quote"]

logger = logging.getLogger(__name__)


def load_daily_quote(
    *, config: QuotesConfig, today: date | None = None
) -> Quote | None:
    """Load the quotes folder and pick today's quote.

    Never raises: problems are logged as warnings and yield ``None`` so the
    digest is still sent.

    Args:
        config: Quotes settings; the feature is disabled when ``config.dir`` is unset.
        today: Date to pick for. Defaults to the current UTC date.

    Returns:
        The day's quote, or ``None`` when disabled or no valid quote exists.
    """
    if config.dir is None:
        return None
    if not config.dir.is_dir():
        logger.warning("Quotes path %s is not a directory, skipping quote", config.dir)
        return None
    try:
        quotes = ObsidianQuoteProvider(config=config).load()
    except Exception as e:  # the quote must never break the digest
        logger.warning("Failed to load quotes, skipping quote: %s", e, exc_info=True)
        return None
    if not quotes:
        logger.warning("No valid quotes found in %s, skipping quote", config.dir)
        return None
    return pick_daily(quotes=quotes, today=today or datetime.now(tz=UTC).date())
