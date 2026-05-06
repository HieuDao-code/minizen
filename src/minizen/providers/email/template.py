"""Email template renderer -- converts Markdown digest to styled HTML and plain text."""

import math
import re
from datetime import UTC, datetime
from html import escape, unescape
from importlib.metadata import version as pkg_version
from typing import TYPE_CHECKING, cast

import mistune

if TYPE_CHECKING:
    from minizen.providers.rss.miniflux import Article

# Colour palette
_BG = "#EEF2F7"
_CARD_BG = "#FFFFFF"
_TEXT = "#1E2D3D"
_ACCENT_BLUE = "#2D7DD2"
_ACCENT_ORANGE = "#D4622A"
_BORDER = "#D4DCE8"
_MUTED = "#5A6A7A"
_HEADER_BG = "#1E2D3D"
_HEADER_TEXT = "#FFFFFF"


def _reading_time(markdown: str) -> int:
    """Estimate reading time in minutes assuming 200 words per minute.

    Args:
        markdown: Raw Markdown text to measure.

    Returns:
        Estimated reading time in whole minutes, minimum 1.
    """
    words = len(markdown.split())
    return max(1, math.ceil(words / 200))


def _build_article_cards(html: str) -> str:
    """Wrap each article section in a styled card div and convert feed names to badges.

    Scans for ``<p><strong>Feed Name</strong></p>`` patterns (the feed name line
    produced by the AI template) and groups each with its following content into a
    card ``<div>``. Content before the first feed name becomes the intro block.

    Args:
        html: Raw HTML produced by mistune from the AI Markdown digest.

    Returns:
        HTML with article sections wrapped in card divs and feed names as badge spans.
    """
    badge_pattern = re.compile(r"<p><strong>(.*?)</strong></p>", re.DOTALL)
    parts = badge_pattern.split(html)

    # parts[0] = intro text
    # parts[1], parts[2] = first feed name, first article body
    # parts[3], parts[4] = second feed name, second article body, etc.
    result = parts[0]

    for i in range(1, len(parts), 2):
        feed_name = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        result += (
            f'<div class="article-card">'
            f'<span class="feed-badge">{escape(unescape(feed_name))}</span>'
            f"{content}"
            f"</div>"
        )

    return result


def _build_more_links(articles: list[Article]) -> str:
    """Build a compact "More to read" link list for articles without full summaries.

    Args:
        articles: Articles to list. Returns an empty string when the list is empty.

    Returns:
        An HTML ``<div>`` containing a heading and ``<ul>`` of linked titles,
        or an empty string if ``articles`` is empty.
    """
    if not articles:
        return ""
    items = "".join(
        f'<li><a href="{escape(a.url)}">{escape(a.title)}</a></li>'
        for a in articles
        if a.url.startswith(("https://", "http://"))
    )
    if not items:
        return ""
    return f'<div class="more-links"><h3>More to read</h3><ul>{items}</ul></div>'


def render_email(
    markdown: str, *, extra_articles: list[Article] | None = None
) -> tuple[str, str]:
    """Render a Markdown digest into a styled HTML email and a plain-text fallback.

    Args:
        markdown: Raw Markdown digest produced by the AI agent.
        extra_articles: Articles not selected for full summaries, shown as a compact
            link list at the bottom of the email. Defaults to no link list.

    Returns:
        A ``(html, plain_text)`` tuple where ``html`` is a fully styled email
        document and ``plain_text`` is the original Markdown unchanged.
    """
    today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
    read_time = _reading_time(markdown)
    minizen_version = pkg_version("minizen")
    raw_html = cast("str", mistune.html(markdown))
    content_html = _build_article_cards(raw_html)
    more_html = _build_more_links(extra_articles or [])
    preheader = f"~{read_time} min read \u00b7 Your curated articles for {today}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body {{ margin:0; padding:0; }}
    img {{ border:0; display:block; }}

    body {{
      background: {_BG};
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: {_TEXT};
      font-size: 16px;
      line-height: 1.6;
    }}
    .wrapper {{
      max-width: 620px;
      margin: 32px auto;
      background: {_BG};
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }}
    .header {{
      background: {_HEADER_BG};
      padding: 36px 32px 28px;
      color: {_HEADER_TEXT};
    }}
    .header-label {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      opacity: 0.65;
      margin: 0 0 8px;
    }}
    .header h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
      color: {_HEADER_TEXT};
    }}
    .header .meta {{
      margin: 0;
      font-size: 14px;
      opacity: 0.7;
      color: {_HEADER_TEXT};
    }}
    .content {{
      padding: 32px 32px 24px;
    }}
    .content > p {{
      font-size: 16px;
      line-height: 1.8;
      color: {_TEXT};
      margin: 0 0 24px;
    }}
    .article-card {{
      background: {_CARD_BG};
      border: 1px solid {_BORDER};
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 16px;
    }}
    .feed-badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: {_ACCENT_ORANGE};
      margin-bottom: 8px;
    }}
    .article-card h2 {{
      font-size: 18px;
      font-weight: 700;
      color: {_TEXT};
      margin: 0 0 12px;
      line-height: 1.3;
    }}
    .article-card h2 a {{
      color: {_ACCENT_BLUE};
      text-decoration: none;
    }}
    .article-card h2 a:hover {{ text-decoration: underline; }}
    .article-card p {{
      font-size: 15px;
      line-height: 1.75;
      color: {_TEXT};
      margin: 0 0 12px;
    }}
    .article-card a {{
      color: {_ACCENT_BLUE};
      text-decoration: none;
      font-weight: 500;
    }}
    .article-card a:hover {{ text-decoration: underline; }}
    .content hr {{
      border: none;
      border-top: 1px solid {_BORDER};
      margin: 28px 0;
    }}
    .footer {{
      background: {_BG};
      border-top: 1px solid {_BORDER};
      padding: 20px 32px;
      font-size: 13px;
      color: {_MUTED};
      text-align: center;
    }}
    .footer a {{
      color: {_ACCENT_BLUE};
      text-decoration: none;
      font-weight: 600;
    }}
    .footer .version {{
      display: block;
      margin-top: 4px;
      font-size: 11px;
      opacity: 0.7;
    }}

    .more-links {{
      margin-top: 28px;
      padding-top: 20px;
      border-top: 1px solid {_BORDER};
    }}
    .more-links h3 {{
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: {_MUTED};
      margin: 0 0 12px;
    }}
    .more-links ul {{
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .more-links li {{
      margin-bottom: 6px;
      font-size: 14px;
    }}
    .more-links li a {{
      color: {_ACCENT_BLUE};
      text-decoration: none;
    }}
    .more-links li a:hover {{ text-decoration: underline; }}

    @media (max-width: 640px) {{
      .wrapper {{ margin: 0; border-radius: 0; box-shadow: none; }}
      .header {{ padding: 28px 20px 22px; }}
      .header h1 {{ font-size: 24px; }}
      .content {{ padding: 24px 20px 20px; }}
      .article-card {{ padding: 18px; }}
      .article-card h2 {{ font-size: 17px; }}
      .footer {{ padding: 16px 20px; }}
    }}
  </style>
</head>
<body>
  <span style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{preheader}</span>
  <div class="wrapper">
    <div class="header">
      <p class="header-label">minizen</p>
      <h1>Your Daily Zen</h1>
      <p class="meta">{today} &middot; ~{read_time} min read</p>
    </div>
    <div class="content">
      {content_html}
      {more_html}
    </div>
    <div class="footer">
      Curated by <a href="https://hieudao-code.github.io/minizen/">minizen</a> &middot; {today}
      <span class="version">v{minizen_version}</span>
    </div>
  </div>
</body>
</html>"""

    return html, markdown
