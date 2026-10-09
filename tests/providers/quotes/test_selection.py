"""Tests for minizen.providers.quotes.selection daily quote picking."""

from datetime import date, timedelta

from minizen.providers.quotes.obsidian import Quote
from minizen.providers.quotes.selection import pick_daily


def _make_quotes(count: int) -> list[Quote]:
    return [Quote(text=f"q{i}", author="A", source="S") for i in range(count)]


def test_pick_daily_is_stable_for_the_same_date() -> None:
    # arrange
    quotes = _make_quotes(count=7)

    # act
    first = pick_daily(quotes=quotes, today=date(2026, 10, 9))
    second = pick_daily(quotes=list(quotes), today=date(2026, 10, 9))

    # assert
    assert first == second


def test_pick_daily_shows_every_quote_once_per_cycle() -> None:
    # arrange
    quotes = _make_quotes(count=7)
    start = date(2026, 10, 9)

    # act
    picks = [
        pick_daily(quotes=quotes, today=start + timedelta(days=offset))
        for offset in range(len(quotes))
    ]

    # assert
    assert sorted(p.text for p in picks if p is not None) == sorted(
        q.text for q in quotes
    )


def test_pick_daily_returns_none_for_no_quotes() -> None:
    # act
    quote = pick_daily(quotes=[], today=date(2026, 10, 9))

    # assert
    assert quote is None
