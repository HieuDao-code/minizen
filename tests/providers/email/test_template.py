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
