"""Tests for minizen.providers.email.template email rendering."""

from datetime import UTC, datetime
from pathlib import Path

from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import Article


def test_render_email_returns_html_and_plain_text() -> None:
    # act
    html, plain_text = render_email(markdown="## Hello\n\nWorld")

    # assert
    assert "<html" in html
    assert "Hello" in html
    assert plain_text == "## Hello\n\nWorld"


def test_render_email_html_contains_date_and_read_time() -> None:
    # act
    html, _ = render_email(markdown="word " * 200)

    # assert
    assert "min read" in html


def test_render_email_html_contains_minizen_version() -> None:
    # act
    html, _ = render_email(markdown="content")

    # assert
    assert "minizen" in html


def test_render_email_with_fixture_digest() -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "digest_result.md"
    content = fixture_path.read_text()

    # act
    html, plain_text = render_email(markdown=content)

    # assert
    assert "#2D7DD2" in html  # accent blue
    assert "#EEF2F7" in html  # background
    assert "#D4622A" in html  # accent orange
    assert "#1E2D3D" in html  # text / header bg
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
        "[Read ->](https://example.com)\n"
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
        "[Read ->](https://example.com)\n"
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


def test_render_email_with_extra_articles_shows_link_list() -> None:
    # arrange
    extra = Article(
        id=99,
        title="Extra Article Title",
        url="https://example.com/extra",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[extra])

    # assert
    assert "More to read" in html
    assert "Extra Article Title" in html
    assert "https://example.com/extra" in html


def test_render_email_with_no_extra_articles_hides_link_list() -> None:
    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[])

    # assert
    assert "More to read" not in html


def test_render_email_escapes_article_title_in_more_links() -> None:
    # arrange
    extra = Article(
        id=1,
        title="<script>alert('xss')</script>",
        url="https://example.com/article",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[extra])

    # assert
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_email_escapes_article_url_in_more_links() -> None:
    # arrange
    extra = Article(
        id=2,
        title="Safe Title",
        url='https://example.com/a"onmouseover="alert(1)',
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[extra])

    # assert
    assert 'onmouseover="alert(1)' not in html
    assert "&quot;" in html


def test_render_email_blocks_javascript_url_in_more_links() -> None:
    # arrange
    extra = Article(
        id=3,
        title="Malicious Link",
        url="javascript:alert('xss')",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[extra])

    # assert
    assert 'href="javascript:' not in html
    assert 'href="#"' in html
