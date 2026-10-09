"""Tests for minizen.providers.email.template email rendering."""

from datetime import UTC, datetime
from pathlib import Path

from minizen.providers.email.template import render_email
from minizen.providers.quotes import Quote
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
    assert "~1 min read" in html
    assert "Also covered by" in html
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


def test_render_email_shows_feed_name_in_more_links() -> None:
    # arrange
    extra = Article(
        id=99,
        title="Extra Article Title",
        url="https://example.com/extra",
        content="content",
        feed_name="My Source Feed",
        published_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[extra])

    # assert
    assert "My Source Feed" in html
    assert 'class="feed-badge"' in html


def test_render_email_escapes_feed_name_in_more_links() -> None:
    # arrange
    extra = Article(
        id=4,
        title="Normal Title",
        url="https://example.com/article",
        content="content",
        feed_name='<script>alert("xss")</script>',
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_email_escapes_article_title_in_more_links() -> None:
    # arrange
    extra = Article(
        id=1,
        title='<script>alert("xss")</script>',
        url="https://example.com/article",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_email_escapes_article_url_in_more_links() -> None:
    # arrange
    extra = Article(
        id=2,
        title="Normal Title",
        url='https://example.com/path?q=<"injected">',
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert '<"injected">' not in html
    assert "&lt;" in html


def test_render_email_filters_javascript_url_in_more_links() -> None:
    # arrange
    extra = Article(
        id=3,
        title="Malicious",
        url="javascript:alert(1)",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert "More to read" not in html


def test_render_email_escapes_feed_name_in_article_cards() -> None:
    # arrange
    markdown = (
        "Intro.\n\n**<b>evil</b>**\n\n## [Title](https://example.com)\n\nSummary.\n"
    )

    # act
    html, _ = render_email(markdown=markdown)

    # assert
    assert 'class="feed-badge"><b>evil</b>' not in html
    assert "&lt;b&gt;evil&lt;/b&gt;" in html


def test_render_email_has_no_intro_paragraph_before_first_card() -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "digest_result.md"
    content = fixture_path.read_text()

    # act
    html, _ = render_email(markdown=content)

    # assert
    content_start = html.index('<div class="content">')
    first_card = html.index('<div class="article-card">')
    assert "<p" not in html[content_start:first_card]


def test_render_email_adds_quote_card_to_html() -> None:
    # arrange
    quote = Quote(
        text="I must not fear.\nFear is the mind-killer.",
        author="Frank Herbert",
        source="Dune",
    )

    # act
    html, _ = render_email(markdown="## Digest", quote=quote)

    # assert
    assert 'class="quote-card"' in html
    assert "I must not fear.<br>Fear is the mind-killer." in html
    assert "&mdash; Frank Herbert, <em>Dune</em>" in html


def test_render_email_places_quote_card_after_more_links_before_footer() -> None:
    # arrange
    article = Article(
        id=1,
        title="Extra",
        url="https://example.com/1",
        content="Content",
        feed_name="Feed",
        published_at=datetime(2026, 4, 25, tzinfo=UTC),
    )
    quote = Quote(
        text="Honor is dead.", author="Brandon Sanderson", source="Words of Radiance"
    )

    # act
    html, _ = render_email(markdown="## Digest", extra_articles=[article], quote=quote)

    # assert
    assert (
        html.index('class="more-links"')
        < html.index('class="quote-card"')
        < html.index('class="footer"')
    )


def test_render_email_escapes_quote_html() -> None:
    # arrange
    quote = Quote(text="<script>alert(1)</script> & co", author="A <b>", source="S & T")

    # act
    html, plain_text = render_email(markdown="## Digest", quote=quote)

    # assert
    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; co" in html
    assert "&mdash; A &lt;b&gt;, <em>S &amp; T</em>" in html
    assert "<script>alert(1)</script> & co" in plain_text


def test_render_email_appends_quote_to_plain_text() -> None:
    # arrange
    quote = Quote(
        text="I must not fear.\nFear is the mind-killer.",
        author="Frank Herbert",
        source="Dune",
    )

    # act
    _, plain_text = render_email(markdown="## Digest", quote=quote)

    # assert
    assert plain_text == (
        "## Digest\n\n---\n\n"
        "> I must not fear.\n> Fear is the mind-killer.\n\n"
        "— Frank Herbert, *Dune*"
    )


def test_render_email_without_quote_has_no_quote_card() -> None:
    # act
    html, plain_text = render_email(markdown="## Digest")

    # assert
    assert 'class="quote-card"' not in html
    assert plain_text == "## Digest"
