from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings
from minizen.core.pipeline import run_pipeline
from minizen.providers.rss.miniflux import Article


def _make_settings() -> Settings:
    return Settings(
        miniflux=MinifluxConfig(url="https://rss.example.com", api_key="key"),
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="from@example.com",
            to_addr="to@example.com",
            username="user",
            password="pass",
        ),
        ai=AIConfig(model="anthropic:claude-sonnet-4-6", top_n=2),
    )


def _make_article(article_id: int) -> Article:
    return Article(
        id=article_id,
        title=f"Article {article_id}",
        url=f"https://example.com/{article_id}",
        content="Content",
        feed_name="Feed",
        published_at=datetime(2026, 4, 25, tzinfo=UTC),
    )


def test_pipeline_runs_full_flow(mocker: MockerFixture) -> None:
    # arrange
    articles = [_make_article(1), _make_article(2)]
    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = articles
    mock_email = MagicMock()
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1, 2]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
    mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    settings = _make_settings()

    # act
    run_pipeline(settings=settings)

    # assert
    today = date.today().strftime("%B %-d, %Y")
    mock_rss.fetch_unread.assert_called_once_with()
    mock_agent.run.assert_called_once_with(articles=articles)
    mock_email.send.assert_called_once_with(
        subject=f"Your Daily Zen — {today}",
        html="<h2>Digest</h2>",
        plain_text="## Digest",
    )
    mock_rss.mark_as_read.assert_called_once_with(article_ids=[1, 2])


def test_pipeline_exits_early_when_no_articles(mocker: MockerFixture) -> None:
    # arrange
    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = []
    mock_email = MagicMock()
    mock_agent = MagicMock()
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
    settings = _make_settings()

    # act
    run_pipeline(settings=settings)

    # assert
    mock_agent.run.assert_not_called()
    mock_email.send.assert_not_called()
    mock_rss.mark_as_read.assert_not_called()


def test_pipeline_does_not_mark_read_when_email_fails(mocker: MockerFixture) -> None:
    # arrange
    articles = [_make_article(1)]
    mock_rss = MagicMock()
    mock_rss.fetch_unread.return_value = articles
    mock_email = MagicMock()
    mock_email.send.side_effect = OSError("SMTP error")
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
    mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    settings = _make_settings()

    # act / assert
    with pytest.raises(OSError, match="SMTP error"):
        run_pipeline(settings=settings)
    mock_rss.mark_as_read.assert_not_called()
