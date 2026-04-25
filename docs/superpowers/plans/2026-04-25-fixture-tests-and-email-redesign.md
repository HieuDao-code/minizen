# Fixture-Based Integration Tests & Email Template Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add realistic hand-crafted fixture files and three fixture-based integration tests, and retheme the email template with a calm sage-and-linen palette.

**Architecture:** Fixture files live in `tests/fixtures/` and are loaded from disk inside each test using `Path(__file__).parents[N] / "fixtures"`. The email redesign follows TDD: write a failing test asserting the new CSS palette tokens, then update `template.py` to make it pass. No new test files are created — all tests are added to existing files.

**Tech Stack:** Python 3.14, pytest, pytest-mock, pydantic, mistune, pathlib

---

## File Structure

| File | Action | Purpose |
|---|---|---|
| `tests/fixtures/miniflux_response.json` | Create | Realistic Miniflux API response, 5 articles, 3 feeds |
| `tests/fixtures/digest_result.md` | Create | Realistic LLM digest, ~450 words, 5 sections |
| `tests/providers/rss/test_miniflux.py` | Modify | Add `test_fetch_unread_with_fixture_data` |
| `tests/providers/email/test_template.py` | Modify | Add `test_render_email_with_fixture_digest` (drives redesign) |
| `src/minizen/providers/email/template.py` | Modify | Retheme CSS with sage/linen palette, remove dark mode block |
| `tests/core/test_pipeline.py` | Modify | Add `test_pipeline_sends_email_with_fixture_data` |

---

## Task 1: Create fixture files

**Files:**
- Create: `tests/fixtures/miniflux_response.json`
- Create: `tests/fixtures/digest_result.md`

- [ ] **Step 1: Create `tests/fixtures/miniflux_response.json`**

```json
{
  "total": 5,
  "entries": [
    {
      "id": 101,
      "title": "Rust's async ecosystem reaches maturity",
      "url": "https://blog.rust-lang.org/2026/04/async-maturity",
      "content": "<p>After years of incremental improvements, Rust's async ecosystem has reached a state of maturity that makes it viable for production workloads. The tokio runtime, async-std, and smol have all stabilised their APIs, and the standard library's async traits are now available on stable Rust.</p><p>In benchmarks conducted by the Rust foundation, async Rust outperforms equivalent Go code by 15–30% in throughput-heavy scenarios while maintaining memory safety guarantees. The main remaining challenge is compile times, which the team is actively addressing through incremental compilation improvements.</p><p>Migration guides from synchronous codebases are now available, and the community has coalesced around a set of best practices that make async Rust significantly more approachable than it was two years ago.</p>",
      "feed": {"title": "Hacker News"},
      "published_at": "2026-04-25T07:30:00Z"
    },
    {
      "id": 102,
      "title": "The hidden cost of LLM context windows",
      "url": "https://www.anthropic.com/research/context-window-cost",
      "content": "<p>As context windows have grown from 4k to 1M tokens, the economic and environmental costs have scaled in unexpected ways. A new paper from researchers at Anthropic and Stanford examines how quadratic attention complexity makes large-context inference disproportionately expensive.</p><p>The paper introduces a new metric, \"effective context utilization,\" which measures how much of a given context window actually influences the model output. Surprisingly, most real-world tasks use fewer than 10% of available tokens effectively, suggesting that smarter retrieval strategies could reduce costs by an order of magnitude.</p><p>The authors propose a hybrid approach combining sparse attention with dense retrieval, achieving 90% of full-context accuracy at 8% of the compute cost in their experiments.</p>",
      "feed": {"title": "Hacker News"},
      "published_at": "2026-04-25T06:15:00Z"
    },
    {
      "id": 103,
      "title": "Apple's M4 Ultra sets new records in creative workloads",
      "url": "https://www.theverge.com/2026/4/25/apple-m4-ultra-review",
      "content": "<p>Apple's M4 Ultra chip, shipping inside the new Mac Pro, has set records across every creative benchmark tested. Video transcoding, 3D rendering, and machine learning inference all show generational improvements over the M3 Ultra, with the chip drawing roughly the same peak power.</p><p>The unified memory architecture has been expanded to 256GB maximum, which finally makes the Mac Pro competitive with high-end workstations for tasks that require keeping large datasets in RAM. Film editors working with 8K RAW footage report that the machine feels qualitatively more fluid, not just faster.</p>",
      "feed": {"title": "The Verge"},
      "published_at": "2026-04-24T18:00:00Z"
    },
    {
      "id": 104,
      "title": "Social media's attention economy is quietly shifting",
      "url": "https://www.theverge.com/2026/4/24/attention-economy-shift",
      "content": "<p>A confluence of regulatory pressure, user fatigue, and competition from AI-native products is reshaping how social platforms optimise for engagement. Several major platforms have quietly rolled back algorithmic amplification of outrage-inducing content following EU Digital Services Act enforcement actions.</p><p>Internal metrics shared with researchers show that reducing inflammatory content recommendation decreased daily active user time by 4%, but improved 30-day retention by 11%. The finding challenges the assumption that maximising session length maximises platform value.</p>",
      "feed": {"title": "The Verge"},
      "published_at": "2026-04-24T14:30:00Z"
    },
    {
      "id": 105,
      "title": "Webb telescope finds unexpected chemistry on TRAPPIST-1e",
      "url": "https://arstechnica.com/science/2026/04/webb-trappist-chemistry",
      "content": "<p>New spectroscopic data from the James Webb Space Telescope has detected sulfur dioxide and water vapour in the atmosphere of TRAPPIST-1e, a rocky exoplanet in its star's habitable zone. While not conclusive evidence of life, the chemical signature is inconsistent with purely geological processes according to two independent research teams.</p><p>The detection required combining 47 transit observations taken over 14 months. Dr. Elena Marchetti, lead author of the Nature paper, cautions that abiotic sources of SO₂ cannot yet be ruled out, but notes that the observed ratio of sulfur isotopes is \"anomalous and worth investigating urgently.\" A follow-up observing campaign has been approved for 2027.</p>",
      "feed": {"title": "Ars Technica"},
      "published_at": "2026-04-24T10:00:00Z"
    }
  ]
}
```

- [ ] **Step 2: Create `tests/fixtures/digest_result.md`**

```markdown
Today's digest covers developments across software engineering, AI research, hardware, and science — a quieter day with a few standout stories worth your attention.

## Rust's async story is finally complete

After years of fragmentation and API churn, Rust's async ecosystem has stabilised around tokio and the new standard library async traits. If you have been waiting for the right moment to adopt async Rust in production, that moment has arrived. The community has converged on clear best practices, and the Rust Foundation's benchmarks show meaningful throughput advantages over Go in I/O-heavy workloads without sacrificing memory safety. [Read the full post](https://blog.rust-lang.org/2026/04/async-maturity)

## Most LLM context goes unused

A joint paper from Anthropic and Stanford researchers introduces a sobering metric: effective context utilization. Their finding — that most real-world tasks use fewer than 10% of available context tokens productively — reframes the arms race for ever-larger context windows. The proposed hybrid of sparse attention and dense retrieval achieves 90% of full-context accuracy at 8% of the compute cost. Worth reading if you are building systems that rely on large contexts. [Full paper summary](https://www.anthropic.com/research/context-window-cost)

## Apple's M4 Ultra is a genuine leap for creative work

The M4 Ultra in the new Mac Pro is not just incrementally faster — film editors describe it as qualitatively different for 8K RAW workflows. The jump to 256GB unified memory is the headline spec, but the real story is that the machine stays within the same power envelope as the M3 generation. If you are in the market for a high-end creative workstation, the Mac Pro is now a serious contender against x86 workstations for memory-intensive tasks. [The Verge review](https://www.theverge.com/2026/4/25/apple-m4-ultra-review)

## Platforms quietly dialling back outrage amplification

Buried in a broader piece on the attention economy: several major platforms have reduced algorithmic amplification of inflammatory content following EU DSA enforcement. Session time dropped 4%, but 30-day retention improved 11%. The data suggests that optimising for engagement duration and optimising for platform health are not the same thing — and regulators may have accidentally forced a better business outcome. [The Verge](https://www.theverge.com/2026/4/24/attention-economy-shift)

## Webb finds unusual chemistry on TRAPPIST-1e

The James Webb Space Telescope detected sulfur dioxide and water vapour in the atmosphere of TRAPPIST-1e after combining 47 transit observations. The sulfur isotope ratio is described as anomalous by the lead researcher. This is not evidence of life, but it is evidence that something unusual is happening chemically on a planet in the habitable zone of its star — and a follow-up campaign is already approved for 2027. One to watch. [Ars Technica](https://arstechnica.com/science/2026/04/webb-trappist-chemistry)
```

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/
git commit -m "test: add realistic fixture files for RSS and LLM digest"
```

---

## Task 2: RSS fixture test

**Files:**
- Modify: `tests/providers/rss/test_miniflux.py`

- [ ] **Step 1: Add the fixture test**

Append to `tests/providers/rss/test_miniflux.py`:

```python
import json
from pathlib import Path

from datetime import UTC


def test_fetch_unread_with_fixture_data(mocker: MockerFixture) -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "miniflux_response.json"
    fixture = json.loads(fixture_path.read_text())
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = fixture
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert len(articles) == 5
    feed_names = {a.feed_name for a in articles}
    assert feed_names == {"Hacker News", "The Verge", "Ars Technica"}
    assert all(a.title for a in articles)
    assert all(a.url for a in articles)
    assert all(a.published_at.tzinfo is UTC for a in articles)
```

Note: `json` and `Path` are not yet imported at the top of `test_miniflux.py`. Add them to the existing imports block:

```python
import json
from datetime import UTC, datetime
from pathlib import Path
```

(The existing file already imports `UTC` and `datetime` — only add `json` and `Path` if missing.)

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/providers/rss/test_miniflux.py::test_fetch_unread_with_fixture_data -v
```

Expected: PASS — the fixture matches the shape `fetch_unread()` already knows how to parse.

- [ ] **Step 3: Commit**

```bash
git add tests/providers/rss/test_miniflux.py
git commit -m "test: add fixture-based RSS parsing integration test"
```

---

## Task 3: Email template redesign (TDD)

**Files:**
- Modify: `tests/providers/email/test_template.py`
- Modify: `src/minizen/providers/email/template.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/providers/email/test_template.py`:

```python
from pathlib import Path


def test_render_email_with_fixture_digest() -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "digest_result.md"
    content = fixture_path.read_text()

    # act
    html, plain_text = render_email(markdown=content)

    # assert
    assert "#7A9E7E" in html
    assert "#F2EFE9" in html
    assert "## Rust" in html
    assert "## Most LLM" in html
    assert "## Apple" in html
    assert "## Platforms" in html
    assert "## Webb" in html
    assert "~3 min read" in html
    assert plain_text == content
```

Note: `Path` may not be imported in `test_template.py`. Add it:

```python
from pathlib import Path
```

- [ ] **Step 2: Run to confirm it fails**

```bash
uv run pytest tests/providers/email/test_template.py::test_render_email_with_fixture_digest -v
```

Expected: FAIL — `AssertionError` on `"#7A9E7E" in html` (current template has old colors).

- [ ] **Step 3: Retheme `src/minizen/providers/email/template.py`**

Replace the entire `<style>` block and remove the dark mode media query. The full updated CSS section (replace everything between `<style>` and `</style>`):

```css
    body { margin:0; padding:0; }
    img { border:0; display:block; }

    body {
      background: #F2EFE9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #2E2A25;
      font-size: 16px;
      line-height: 1.6;
    }
    .wrapper {
      max-width: 620px;
      margin: 32px auto;
      background: #FAFAF8;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }
    .header {
      background: linear-gradient(135deg, #F2EFE9 0%, #C8B89A 50%, #9E8A72 100%);
      padding: 36px 32px 28px;
      color: #2E2A25;
    }
    .header-label {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      opacity: 0.65;
      margin: 0 0 8px;
    }
    .header h1 {
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
    }
    .header .meta {
      margin: 0;
      font-size: 14px;
      opacity: 0.7;
    }
    .content {
      padding: 32px 32px 24px;
    }
    .content h1 {
      font-size: 22px;
      font-weight: 700;
      color: #2E2A25;
      margin: 28px 0 6px;
      line-height: 1.3;
    }
    .content h2 {
      font-size: 18px;
      font-weight: 700;
      color: #2E2A25;
      margin: 36px 0 8px;
      padding-left: 12px;
      border-left: 4px solid #7A9E7E;
      line-height: 1.3;
    }
    .content p {
      font-size: 16px;
      line-height: 1.8;
      color: #2E2A25;
      margin: 8px 0 18px;
    }
    .content a {
      color: #6B8F6E;
      text-decoration: none;
      font-weight: 500;
    }
    .content a:hover { text-decoration: underline; }
    .content strong { color: #2E2A25; font-weight: 600; }
    .content em { color: #6B6560; }
    .content hr {
      border: none;
      border-top: 1px solid #D4CEC8;
      margin: 28px 0;
    }
    .content ul, .content ol {
      padding-left: 20px;
      color: #2E2A25;
      font-size: 16px;
      line-height: 1.8;
    }
    .content blockquote {
      border-left: 3px solid #C8B89A;
      margin: 16px 0;
      padding: 4px 16px;
      color: #6B6560;
      font-style: italic;
    }
    .footer {
      background: #EAE5DC;
      border-top: 1px solid #D4CEC8;
      padding: 20px 32px;
      font-size: 13px;
      color: #6B6560;
      text-align: center;
    }
    .footer a {
      color: #7A9E7E;
      text-decoration: none;
      font-weight: 600;
    }
    .footer .version {
      display: block;
      margin-top: 4px;
      font-size: 11px;
      opacity: 0.7;
    }

    @media (max-width: 640px) {
      .wrapper { margin: 0; border-radius: 0; box-shadow: none; }
      .header { padding: 28px 20px 22px; }
      .header h1 { font-size: 24px; }
      .content { padding: 24px 20px 20px; }
      .content h1 { font-size: 20px; }
      .content h2 { font-size: 17px; }
      .content p, .content ul, .content ol { font-size: 17px; line-height: 1.85; }
      .footer { padding: 16px 20px; }
    }
```

The `@media (prefers-color-scheme: dark)` block that follows is removed entirely — do not keep it.

- [ ] **Step 4: Run the test suite**

```bash
uv run pytest tests/providers/email/ -v
```

Expected: all tests PASS, including the new fixture test.

- [ ] **Step 5: Commit**

```bash
git add tests/providers/email/test_template.py src/minizen/providers/email/template.py
git commit -m "feat: retheme email template with sage/linen palette and add fixture test"
```

---

## Task 4: Pipeline fixture test

**Files:**
- Modify: `tests/core/test_pipeline.py`

- [ ] **Step 1: Add the fixture test**

The test imports needed at the top of `tests/core/test_pipeline.py` — add any missing ones:

```python
import json
from pathlib import Path
from unittest.mock import call
```

(`json` and `Path` may not be imported yet. `call` is already imported via `unittest.mock` if used elsewhere — check first, only add what is missing.)

Append the following test to `tests/core/test_pipeline.py`:

```python
def test_pipeline_sends_email_with_fixture_data(mocker: MockerFixture) -> None:
    # arrange
    fixtures = Path(__file__).parents[1] / "fixtures"
    raw = json.loads((fixtures / "miniflux_response.json").read_text())
    digest_markdown = (fixtures / "digest_result.md").read_text()

    articles = [
        Article(
            id=entry["id"],
            title=entry["title"],
            url=entry["url"],
            content=entry["content"],
            feed_name=entry["feed"]["title"],
            published_at=datetime.fromisoformat(
                entry["published_at"].replace("Z", "+00:00")
            ),
        )
        for entry in raw["entries"]
    ]
    article_ids = [a.id for a in articles]

    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = articles
    mock_agent = MagicMock()
    mock_agent.run.return_value = MagicMock(
        markdown=digest_markdown,
        articles_used=article_ids,
    )
    mock_email = MagicMock()

    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    from minizen.providers.email import template as email_template
    mocker.patch(
        "minizen.core.pipeline.render_email",
        wraps=email_template.render_email,
    )
    settings = _make_settings()

    # act
    run_pipeline(settings=settings)

    # assert
    today = date.today().strftime("%B %-d, %Y")
    mock_email.send.assert_called_once()
    call_kwargs = mock_email.send.call_args.kwargs
    assert call_kwargs["subject"] == f"Your Daily Zen — {today}"
    assert "Rust" in call_kwargs["html"]
    assert "Webb" in call_kwargs["html"]
    mock_rss.mark_as_read.assert_called_once_with(article_ids=article_ids)
```

- [ ] **Step 2: Run the test**

```bash
uv run pytest tests/core/test_pipeline.py::test_pipeline_sends_email_with_fixture_data -v
```

Expected: PASS.

- [ ] **Step 3: Run the full test suite**

```bash
uv run pytest --tb=short
```

Expected: all tests PASS with 100% coverage.

- [ ] **Step 4: Commit**

```bash
git add tests/core/test_pipeline.py
git commit -m "test: add end-to-end pipeline fixture test with realistic data"
```
