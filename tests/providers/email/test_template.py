"""Tests for minizen.providers.email.template email rendering."""

from pathlib import Path

from minizen.providers.email.template import render_email


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
