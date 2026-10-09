"""Daily quote selection -- a stateless, seeded shuffled cycle."""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from minizen.providers.quotes.obsidian import Quote

_SHUFFLE_SEED = 0x5EED


def pick_daily(*, quotes: list[Quote], today: date) -> Quote | None:
    """Pick the quote of the day.

    Shuffles the quotes with a fixed seed and indexes the result by the date's
    ordinal, so the same date always gives the same quote and every quote is
    shown once per ``len(quotes)`` consecutive days. Adding or removing a quote
    reshuffles the cycle.

    Args:
        quotes: Candidate quotes in a stable order.
        today: The date to pick for.

    Returns:
        The day's quote, or ``None`` when ``quotes`` is empty.
    """
    if not quotes:
        return None
    shuffled = list(quotes)
    random.Random(_SHUFFLE_SEED).shuffle(shuffled)  # noqa: S311
    return shuffled[today.toordinal() % len(shuffled)]
