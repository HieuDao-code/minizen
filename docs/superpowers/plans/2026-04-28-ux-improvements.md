# UX Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise the default article count to 10, add `comments_url` support, enforce a consistent newsletter-style per-article format in the AI prompt, and redesign the email with article cards and a blue/orange palette.

**Architecture:** Four independent, sequential changes — each touching a narrow slice of the codebase. Config constant → data model → AI prompt → email renderer. Tests are written before implementation at every step.

**Tech Stack:** Python, pydantic, pydantic-ai, mistune, pytest, pytest-mock

---

## File Map

| File | Change |
|------|--------|
| `src/minizen/config/defaults.py` | `DEFAULT_TOP_N = 10` |
| `tests/config/test_defaults.py` | Update assertion from `5` → `10` |
| `src/minizen/providers/rss/miniflux.py` | Add `comments_url: str \| None` to `Article`; map from API response |
| `tests/providers/rss/test_miniflux.py` | Add `comments_url` assertions; two new edge-case tests |
| `tests/fixtures/miniflux_response.json` | Add `comments_url` to entries (some populated, some absent) |
| `src/minizen/ai/agent.py` | New `_SYSTEM_PROMPT` with newsletter template; `comments_url` line in articles text |
| `tests/ai/test_agent.py` | Update `_make_article` helper; add comments_url prompt tests |
| `src/minizen/providers/email/template.py` | Colour constants; `_build_article_cards`; updated CSS/HTML |
| `tests/providers/email/test_template.py` | Update palette assertions; add card/badge tests |
| `tests/fixtures/digest_result.md` | Update to newsletter-style format |

---

## Task 1: Raise default article count to 10

**Files:**
- Modify: `tests/config/test_defaults.py`
- Modify: `src/minizen/config/defaults.py`

- [ ] **Step 1: Update the failing test**

In `tests/config/test_defaults.py`, change:

```python
def test_default_top_n() -> None:
    # act / assert
    assert DEFAULT_TOP_N == 10
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/config/test_defaults.py::test_default_top_n -v
```

Expected: FAIL — `assert 5 == 10`

- [ ] **Step 3: Update the constant**

In `src/minizen/config/defaults.py`, change:

```python
DEFAULT_TOP_N: int = 10
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/config/test_defaults.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/minizen/config/defaults.py tests/config/test_defaults.py
git commit -m "feat: raise default top_n from 5 to 10"
```

---

## Task 2: Add `comments_url` to the Article model

**Files:**
- Modify: `tests/providers/rss/test_miniflux.py`
- Modify: `tests/fixtures/miniflux_response.json`
- Modify: `src/minizen/providers/rss/miniflux.py`

- [ ] **Step 1: Update the fixture to include `comments_url`**

In `tests/fixtures/miniflux_response.json`, add `"comments_url"` to each entry. Give the first entry a real URL; leave the second as an empty string; omit the field entirely from the rest:

```json
{
  "id": 101,
  "comments_url": "https://news.ycombinator.com/item?id=12345",
  ...
}
```

```json
{
  "id": 102,
  "comments_url": "",
  ...
}
```

(Leave entries 103–105 without the key at all.)

- [ ] **Step 2: Write failing tests**

Add to `tests/providers/rss/test_miniflux.py`:

```python
def test_fetch_unread_maps_comments_url_when_present(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 42,
                "title": "Test Article",
                "url": "https://example.com/article",
                "content": "<p>Body</p>",
                "feed": {"title": "Example Feed"},
                "published_at": "2026-04-24T08:00:00Z",
                "comments_url": "https://news.ycombinator.com/item?id=99",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert articles[0].comments_url == "https://news.ycombinator.com/item?id=99"


def test_fetch_unread_sets_comments_url_none_when_empty(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 43,
                "title": "Test Article",
                "url": "https://example.com/article",
                "content": "<p>Body</p>",
                "feed": {"title": "Example Feed"},
                "published_at": "2026-04-24T08:00:00Z",
                "comments_url": "",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert articles[0].comments_url is None


def test_fetch_unread_sets_comments_url_none_when_absent(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 44,
                "title": "Test Article",
                "url": "https://example.com/article",
                "content": "<p>Body</p>",
                "feed": {"title": "Example Feed"},
                "published_at": "2026-04-24T08:00:00Z",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert articles[0].comments_url is None
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/providers/rss/test_miniflux.py::test_fetch_unread_maps_comments_url_when_present tests/providers/rss/test_miniflux.py::test_fetch_unread_sets_comments_url_none_when_empty tests/providers/rss/test_miniflux.py::test_fetch_unread_sets_comments_url_none_when_absent -v
```

Expected: FAIL — `Article` has no field `comments_url`

- [ ] **Step 4: Add `comments_url` to the `Article` model and map it**

In `src/minizen/providers/rss/miniflux.py`, update `Article`:

```python
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
```

In `fetch_unread`, add `comments_url` to the `Article(...)` constructor call:

```python
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
        comments_url=entry.get("comments_url") or None,
    )
    for entry in entries
]
```

- [ ] **Step 5: Run all miniflux tests**

```bash
uv run pytest tests/providers/rss/test_miniflux.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/minizen/providers/rss/miniflux.py tests/providers/rss/test_miniflux.py tests/fixtures/miniflux_response.json
git commit -m "feat: add comments_url field to Article model"
```

---

## Task 3: Update AI system prompt to newsletter template

**Files:**
- Modify: `tests/ai/test_agent.py`
- Modify: `src/minizen/ai/agent.py`

- [ ] **Step 1: Update `_make_article` helper and write failing tests**

In `tests/ai/test_agent.py`, update `_make_article` to accept `comments_url`:

```python
def _make_article(*, article_id: int = 1, comments_url: str | None = None) -> Article:
    return Article(
        id=article_id,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
        comments_url=comments_url,
    )
```

Add these tests:

```python
def test_run_includes_comments_url_in_prompt_when_present(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=1, comments_url="https://news.ycombinator.com/item?id=99")]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "https://news.ycombinator.com/item?id=99" in user_prompt


def test_run_omits_comments_url_in_prompt_when_none(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=1, comments_url=None)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Comments URL: None" not in user_prompt
    assert "ycombinator" not in user_prompt
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/ai/test_agent.py::test_run_includes_comments_url_in_prompt_when_present tests/ai/test_agent.py::test_run_omits_comments_url_in_prompt_when_none -v
```

Expected: FAIL — `_make_article` doesn't accept `comments_url`, and prompt doesn't include it

- [ ] **Step 3: Update `_SYSTEM_PROMPT` and articles text in `agent.py`**

Replace `_SYSTEM_PROMPT` in `src/minizen/ai/agent.py`:

```python
_SYSTEM_PROMPT = """\
You are a personal news curator. You receive a list of unread articles and must:
1. Select the top N most important and interesting articles.
2. Write a cohesive Markdown digest following this exact structure.
3. Return the digest and the IDs of the articles you selected.

Start the digest with a short narrative intro paragraph (2–4 sentences). Do not mention
specific articles in the intro.

Then write one section per selected article using this template exactly:

**{feed_name}**

## [{Article Title}]({url})

{2–3 sentence summary. Concise. No bullet points.}

[Read →]({url}) · [Comments]({comments_url})

Rules:
- The feed name must be bold text on its own line above the heading.
- The article title must be a Markdown link to the article URL.
- Omit the [Comments] link entirely if no comments_url is provided for that article.
- Summary: exactly 2–3 sentences, no lists, no sub-headings.
- Be concise. Prioritise articles with broad significance over niche topics.
"""
```

Update the `articles_text` construction in `run` to include `comments_url`:

```python
articles_text = "\n\n---\n\n".join(
    f"ID: {a.id}\n"
    f"Feed: {a.feed_name}\n"
    f"Title: {a.title}\n"
    f"URL: {a.url}\n"
    f"Published: {a.published_at.isoformat()}\n"
    + (f"Comments URL: {a.comments_url}\n" if a.comments_url else "")
    + f"\n{a.content}"
    for a in articles
)
```

- [ ] **Step 4: Run all agent tests**

```bash
uv run pytest tests/ai/test_agent.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/minizen/ai/agent.py tests/ai/test_agent.py
git commit -m "feat: update AI prompt to newsletter-style article template"
```

---

## Task 4: Redesign email template with card layout and new palette

**Files:**
- Modify: `tests/fixtures/digest_result.md`
- Modify: `tests/providers/email/test_template.py`
- Modify: `src/minizen/providers/email/template.py`

- [ ] **Step 1: Update the digest fixture to newsletter format**

Replace `tests/fixtures/digest_result.md` with a newsletter-style version that matches the new AI template. This is what the AI will now produce:

```markdown
Today's digest covers developments across software engineering, AI research, hardware, and science — a quieter day with a few standout stories worth your attention.

**Hacker News**

## [Rust's async story is finally complete](https://blog.rust-lang.org/2026/04/async-maturity)

After years of fragmentation and API churn, Rust's async ecosystem has stabilised around tokio and the new standard library async traits. The Rust Foundation's benchmarks show meaningful throughput advantages over Go in I/O-heavy workloads without sacrificing memory safety. If you have been waiting for the right moment to adopt async Rust in production, that moment has arrived.

[Read →](https://blog.rust-lang.org/2026/04/async-maturity) · [Comments](https://news.ycombinator.com/item?id=12345)

**Hacker News**

## [Most LLM context goes unused](https://www.anthropic.com/research/context-window-cost)

A joint paper from Anthropic and Stanford researchers introduces a sobering metric: effective context utilization. Their finding — that most real-world tasks use fewer than 10% of available context tokens productively — reframes the arms race for ever-larger context windows. The proposed hybrid of sparse attention and dense retrieval achieves 90% of full-context accuracy at 8% of the compute cost.

[Read →](https://www.anthropic.com/research/context-window-cost)

**The Verge**

## [Apple's M4 Ultra is a genuine leap for creative work](https://www.theverge.com/2026/4/25/apple-m4-ultra-review)

The M4 Ultra in the new Mac Pro is not just incrementally faster — film editors describe it as qualitatively different for 8K RAW workflows. The jump to 256GB unified memory is the headline spec, but the real story is that the machine stays within the same power envelope as the M3 generation. If you are in the market for a high-end creative workstation, the Mac Pro is now a serious contender.

[Read →](https://www.theverge.com/2026/4/25/apple-m4-ultra-review)

**The Verge**

## [Platforms quietly dialling back outrage amplification](https://www.theverge.com/2026/4/24/attention-economy-shift)

Several major platforms have reduced algorithmic amplification of inflammatory content following EU DSA enforcement. Session time dropped 4%, but 30-day retention improved 11%. The data suggests that optimising for engagement duration and optimising for platform health are not the same thing.

[Read →](https://www.theverge.com/2026/4/24/attention-economy-shift)

**Ars Technica**

## [Webb finds unusual chemistry on TRAPPIST-1e](https://arstechnica.com/science/2026/04/webb-trappist-chemistry)

The James Webb Space Telescope detected sulfur dioxide and water vapour in the atmosphere of TRAPPIST-1e after combining 47 transit observations. The sulfur isotope ratio is described as anomalous by the lead researcher. This is not evidence of life, but it is evidence that something unusual is happening chemically on a planet in the habitable zone of its star.

[Read →](https://arstechnica.com/science/2026/04/webb-trappist-chemistry)
```

- [ ] **Step 2: Write failing tests**

In `tests/providers/email/test_template.py`, replace `test_render_email_with_fixture_digest` and add card/badge tests:

```python
def test_render_email_with_fixture_digest() -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "digest_result.md"
    content = fixture_path.read_text()

    # act
    html, plain_text = render_email(markdown=content)

    # assert
    assert "#2D7DD2" in html   # accent blue
    assert "#EEF2F7" in html   # background
    assert "#D4622A" in html   # accent orange
    assert "#1E2D3D" in html   # text / header bg
    assert "Rust" in html
    assert "Most LLM" in html
    assert "Apple" in html
    assert "Platforms" in html
    assert "Webb" in html
    assert "~3 min read" in html
    assert plain_text == content


def test_render_email_html_contains_article_cards() -> None:
    # arrange
    markdown = (
        "Intro paragraph.\n\n"
        "**My Feed**\n\n"
        "## [Title One](https://example.com)\n\n"
        "Summary sentence one. Sentence two. Sentence three.\n\n"
        "[Read →](https://example.com)\n"
    )

    # act
    html, _ = render_email(markdown=markdown)

    # assert
    assert 'class="article-card"' in html


def test_render_email_html_contains_feed_badge() -> None:
    # arrange
    markdown = (
        "Intro paragraph.\n\n"
        "**My Feed**\n\n"
        "## [Title One](https://example.com)\n\n"
        "Summary sentence.\n\n"
        "[Read →](https://example.com)\n"
    )

    # act
    html, _ = render_email(markdown=markdown)

    # assert
    assert 'class="feed-badge"' in html
    assert "My Feed" in html


def test_render_email_does_not_use_old_palette() -> None:
    # act
    html, _ = render_email(markdown="## Hello\n\nWorld")

    # assert
    assert "#7A9E7E" not in html
    assert "#F2EFE9" not in html
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/providers/email/test_template.py::test_render_email_with_fixture_digest tests/providers/email/test_template.py::test_render_email_html_contains_article_cards tests/providers/email/test_template.py::test_render_email_html_contains_feed_badge tests/providers/email/test_template.py::test_render_email_does_not_use_old_palette -v
```

Expected: FAIL

- [ ] **Step 4: Rewrite `src/minizen/providers/email/template.py`**

```python
"""Email template renderer — converts Markdown digest to styled HTML and plain text."""

import math
import re
from datetime import date
from importlib.metadata import version as pkg_version

import mistune

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
            f'<span class="feed-badge">{feed_name}</span>'
            f"{content}"
            f"</div>"
        )

    return result


def render_email(markdown: str) -> tuple[str, str]:
    """Render a Markdown digest into a styled HTML email and a plain-text fallback.

    Args:
        markdown: Raw Markdown digest produced by the AI agent.

    Returns:
        A ``(html, plain_text)`` tuple where ``html`` is a fully styled email
        document and ``plain_text`` is the original Markdown unchanged.
    """
    today = date.today().strftime("%B %-d, %Y")
    read_time = _reading_time(markdown)
    minizen_version = pkg_version("minizen")
    raw_html = mistune.html(markdown)
    content_html = _build_article_cards(raw_html)
    preheader = f"~{read_time} min read · Your curated articles for {today}"

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
    </div>
    <div class="footer">
      Curated by <a href="https://hieudao-code.github.io/minizen/">minizen</a> &middot; {today}
      <span class="version">v{minizen_version}</span>
    </div>
  </div>
</body>
</html>"""

    return html, markdown
```

- [ ] **Step 5: Run all email template tests**

```bash
uv run pytest tests/providers/email/test_template.py -v
```

Expected: all PASS

- [ ] **Step 6: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add src/minizen/providers/email/template.py tests/providers/email/test_template.py tests/fixtures/digest_result.md
git commit -m "feat: redesign email with article cards and editorial colour palette"
```
