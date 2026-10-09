"""Tests for minizen.providers.quotes.load_daily_quote."""

import logging
from datetime import date
from typing import TYPE_CHECKING

from minizen.config.models import QuotesConfig
from minizen.providers.quotes import Quote, load_daily_quote

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_load_daily_quote_returns_quote_from_folder(tmp_path: Path) -> None:
    # arrange
    (tmp_path / "Dune.md").write_text(
        "---\nAuthor: Frank Herbert\nSource: Dune\n---\n> I must not fear.\n",
        encoding="utf-8",
    )

    # act
    quote = load_daily_quote(config=QuotesConfig(dir=tmp_path), today=date(2026, 10, 9))

    # assert
    assert quote == Quote(
        text="I must not fear.", author="Frank Herbert", source="Dune"
    )


def test_load_daily_quote_is_silent_when_disabled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # arrange
    caplog.set_level(logging.DEBUG)

    # act
    quote = load_daily_quote(config=QuotesConfig())

    # assert
    assert quote is None
    assert caplog.records == []


def test_load_daily_quote_warns_when_dir_missing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # arrange
    caplog.set_level(logging.WARNING)

    # act
    quote = load_daily_quote(config=QuotesConfig(dir=tmp_path / "missing"))

    # assert
    assert quote is None
    assert "is not a directory" in caplog.text


def test_load_daily_quote_warns_when_dir_is_a_file(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # arrange
    file_path = tmp_path / "quotes.md"
    file_path.write_text("> not a folder\n", encoding="utf-8")
    caplog.set_level(logging.WARNING)

    # act
    quote = load_daily_quote(config=QuotesConfig(dir=file_path))

    # assert
    assert quote is None
    assert "is not a directory" in caplog.text


def test_load_daily_quote_warns_when_no_valid_quotes(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # arrange
    caplog.set_level(logging.WARNING)

    # act
    quote = load_daily_quote(config=QuotesConfig(dir=tmp_path))

    # assert
    assert quote is None
    assert "No valid quotes" in caplog.text
