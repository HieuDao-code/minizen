"""Obsidian quote source -- parses one-quote-per-file Markdown notes."""

import logging
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from pathlib import Path

    from minizen.config.models import QuotesConfig

logger = logging.getLogger(__name__)


class Quote(BaseModel):
    """A single favourite quote with its attribution."""

    model_config = ConfigDict(frozen=True)

    text: str
    author: str
    source: str


def _split_frontmatter(content: str) -> tuple[dict[str, object], list[str]] | None:
    """Split a note into its YAML frontmatter mapping and remaining body lines.

    Args:
        content: Full text of the note.

    Returns:
        ``(frontmatter, body_lines)``, or ``None`` when the note has no
        ``---``-delimited frontmatter or it is not a mapping.

    Raises:
        yaml.YAMLError: If the frontmatter is not valid YAML.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next(
        (i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if end is None:
        return None
    meta = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(meta, dict):
        return None
    return meta, lines[end + 1 :]


def _text_field(meta: dict[str, object], key: str) -> str | None:
    """Return a frontmatter value as stripped text, or ``None`` if empty or absent.

    Args:
        meta: Parsed frontmatter mapping.
        key: Frontmatter key to read.

    Returns:
        The value converted to ``str`` and stripped, or ``None``.
    """
    value = meta.get(key)
    if value is None:
        return None
    return str(value).strip() or None


def parse_quote_file(*, path: Path) -> Quote | None:
    """Parse one Obsidian quote note.

    The quote text is every line starting with ``>`` (marker and one optional
    following space stripped), joined with newlines. Other body content is
    ignored. Never raises: unreadable or invalid notes are logged and skipped.

    Args:
        path: Path to the Markdown note.

    Returns:
        The parsed ``Quote``, or ``None`` if the note is invalid.
    """
    try:
        parsed = _split_frontmatter(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, yaml.YAMLError) as e:
        logger.warning("Skipping quote file %s: %s", path, e)
        return None
    if parsed is None:
        logger.warning("Skipping quote file %s: missing frontmatter", path)
        return None
    meta, body = parsed
    author = _text_field(meta, "Author")
    source = _text_field(meta, "Source")
    if author is None or source is None:
        logger.warning("Skipping quote file %s: missing Author or Source", path)
        return None
    text = "\n".join(
        line[1:].removeprefix(" ") for line in body if line.startswith(">")
    ).strip()
    if not text:
        logger.warning("Skipping quote file %s: no blockquote", path)
        return None
    return Quote(text=text, author=author, source=source)


class ObsidianQuoteProvider:
    """Quote source that reads one-quote-per-file notes from a folder."""

    def __init__(self, *, config: QuotesConfig) -> None:
        """Initialise the provider from the quotes configuration.

        Args:
            config: Quotes settings holding the notes directory.
        """
        self._dir = config.dir

    def load(self) -> list[Quote]:
        """Load all valid quotes from the top level of the configured folder.

        Returns:
            Quotes in filename order; empty when no directory is configured.
        """
        if self._dir is None:
            return []
        quotes = []
        for path in sorted(self._dir.glob("*.md")):
            if not path.is_file():
                continue
            quote = parse_quote_file(path=path)
            if quote is not None:
                quotes.append(quote)
        return quotes
