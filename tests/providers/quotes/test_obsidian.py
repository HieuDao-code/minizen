"""Tests for minizen.providers.quotes.obsidian quote parsing."""

import logging
from typing import TYPE_CHECKING

import pytest

from minizen.config.models import QuotesConfig
from minizen.providers.quotes.obsidian import (
    ObsidianQuoteProvider,
    Quote,
    parse_quote_file,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_note(directory: Path, *, name: str, frontmatter: str, body: str) -> Path:
    path = directory / name
    path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return path


def test_parse_quote_file_reads_frontmatter_and_blockquote(tmp_path: Path) -> None:
    # arrange
    path = _write_note(
        tmp_path,
        name="Dune.md",
        frontmatter="id: Dune\ntags:\n  - quote\nAuthor: Frank Herbert\nSource: Dune",
        body="\n> I must not fear.\n",
    )

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote == Quote(
        text="I must not fear.", author="Frank Herbert", source="Dune"
    )


def test_parse_quote_file_keeps_line_breaks_and_ignores_other_body(
    tmp_path: Path,
) -> None:
    # arrange
    path = _write_note(
        tmp_path,
        name="Dao.md",
        frontmatter="Author: Ken Liu\nSource: Laozi's Dao De Jing",
        body=(
            "\n# Chapter 33\n\n## Winning against yourself\n\nAbout Laozi:\n\n"
            "> Knowing others is cleverness,\n"
            "> but knowing yourself is wisdom.\n"
        ),
    )

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is not None
    assert (
        quote.text == "Knowing others is cleverness,\nbut knowing yourself is wisdom."
    )


def test_parse_quote_file_accepts_marker_without_space(tmp_path: Path) -> None:
    # arrange
    path = _write_note(
        tmp_path,
        name="Sartre.md",
        frontmatter="Author: Jean-Paul Sartre\nSource: Existentialism Is a Humanism",
        body=">Existence precedes essence",
    )

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is not None
    assert quote.text == "Existence precedes essence"


def test_parse_quote_file_keeps_trailing_ellipsis(tmp_path: Path) -> None:
    # arrange
    path = _write_note(
        tmp_path,
        name="Dune 2.md",
        frontmatter="Author: Frank Herbert\nSource: Dune",
        body="\n> It is shocking to find how many people do...\n",
    )

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is not None
    assert quote.text == "It is shocking to find how many people do..."


def test_parse_quote_file_handles_bom_and_crlf(tmp_path: Path) -> None:
    # arrange
    path = tmp_path / "Windows.md"
    path.write_bytes(
        "﻿---\r\nAuthor: Joe Abercrombie\r\nSource: The Blade Itself\r\n---\r\n"
        "\r\n> Well.\r\n> What can we do?\r\n".encode()
    )

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote == Quote(
        text="Well.\nWhat can we do?",
        author="Joe Abercrombie",
        source="The Blade Itself",
    )


def test_parse_quote_file_stringifies_non_string_values(tmp_path: Path) -> None:
    # arrange
    path = _write_note(
        tmp_path,
        name="1984.md",
        frontmatter="Author: George Orwell\nSource: 1984",
        body="\n> Big Brother is watching you.\n",
    )

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is not None
    assert quote.source == "1984"


@pytest.mark.parametrize(
    ("frontmatter", "body"),
    [
        ("Source: Dune", "\n> text\n"),
        ("Author: Frank Herbert", "\n> text\n"),
        ("Author:\nSource: Dune", "\n> text\n"),
        ("Author: Frank Herbert\nSource: Dune", "\nNo blockquote here.\n"),
        ("Author: Frank Herbert\nSource: Dune", "\n>   \n"),
        ("Author: [unclosed\nSource: Dune", "\n> text\n"),
        ("- just\n- a list", "\n> text\n"),
    ],
    ids=[
        "missing-author",
        "missing-source",
        "empty-author",
        "no-blockquote",
        "blank-blockquote",
        "invalid-yaml",
        "non-mapping-frontmatter",
    ],
)
def test_parse_quote_file_skips_invalid_note_with_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    frontmatter: str,
    body: str,
) -> None:
    # arrange
    path = _write_note(tmp_path, name="Bad.md", frontmatter=frontmatter, body=body)
    caplog.set_level(logging.WARNING)

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is None
    assert "Bad.md" in caplog.text


@pytest.mark.parametrize(
    "content",
    ["> Just a quote\n", "---\nAuthor: A\nSource: S\n> never closed\n", ""],
    ids=["no-frontmatter", "unclosed-frontmatter", "empty-file"],
)
def test_parse_quote_file_skips_missing_frontmatter(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, content: str
) -> None:
    # arrange
    path = tmp_path / "Plain.md"
    path.write_text(content, encoding="utf-8")
    caplog.set_level(logging.WARNING)

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is None
    assert "Plain.md" in caplog.text


def test_parse_quote_file_skips_non_utf8_file(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # arrange
    path = tmp_path / "Binary.md"
    path.write_bytes(b"---\nAuthor: \xff\xfe\n---\n> text\n")
    caplog.set_level(logging.WARNING)

    # act
    quote = parse_quote_file(path=path)

    # assert
    assert quote is None
    assert "Binary.md" in caplog.text


def test_provider_loads_sorted_markdown_files_and_skips_invalid(
    tmp_path: Path,
) -> None:
    # arrange
    _write_note(
        tmp_path, name="b.md", frontmatter="Author: B\nSource: SB", body="> two"
    )
    _write_note(
        tmp_path, name="a.md", frontmatter="Author: A\nSource: SA", body="> one"
    )
    _write_note(tmp_path, name="bad.md", frontmatter="Author: X", body="> skipped")
    _write_note(
        tmp_path, name="note.txt", frontmatter="Author: T\nSource: ST", body="> no"
    )
    (tmp_path / "folder.md").mkdir()
    (tmp_path / "sub").mkdir()
    _write_note(
        tmp_path / "sub", name="c.md", frontmatter="Author: C\nSource: SC", body="> no"
    )
    provider = ObsidianQuoteProvider(config=QuotesConfig(dir=tmp_path))

    # act
    quotes = provider.load()

    # assert
    assert quotes == [
        Quote(text="one", author="A", source="SA"),
        Quote(text="two", author="B", source="SB"),
    ]


def test_provider_returns_empty_list_when_disabled() -> None:
    # arrange
    provider = ObsidianQuoteProvider(config=QuotesConfig())

    # act
    quotes = provider.load()

    # assert
    assert quotes == []
