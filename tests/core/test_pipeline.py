"""Tests for the end-to-end digest pipeline."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings
from minizen.core.pipeline import run_pipeline
from minizen.providers.email import template as email_template
from minizen.providers.rss.miniflux import Article

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_settings(
    *,
    interests: list[str] | None = None,
    avoid: list[str] | None = None,
    preferred_categories: list[str] | None = None,
) -> Settings:
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
        ai=AIConfig(
            model="anthropic:claude-sonnet-4-6",
            top_n=2,
            interests=interests or [],
            avoid=avoid or [],
            preferred_categories=preferred_categories or [],
        ),
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


@freeze_time("2026-04-29")
def test_pipeline_runs_full_flow(mocker: MockerFixture) -> None:
    # arrange
    articles = [_make_article(1), _make_article(2), _make_article(3)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_email = MagicMock()
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1, 2]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mock_render = mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mock_agent_cls = mocker.patch(
        "minizen.core.pipeline.DigestAgent", return_value=mock_agent
    )
    settings = _make_settings()

    # act
    run_pipeline(settings=settings)

    # assert
    mock_rss.fetch_recent.assert_called_once_with()
    mock_agent.run.assert_called_once_with(articles=articles)
    extra = [a for a in articles if a.id not in {1, 2}]
    mock_render.assert_called_once_with("## Digest", extra_articles=extra)
    mock_email.send.assert_called_once_with(
        subject="Your Daily Zen — April 29, 2026",
        html="<h2>Digest</h2>",
        plain_text="## Digest",
    )
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=2,
        max_words_per_article=500,
        interests=[],
        avoid=[],
        preferred_categories=[],
    )


def test_pipeline_exits_early_when_no_articles(mocker: MockerFixture) -> None:
    # arrange
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
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


@freeze_time("2026-04-29")
def test_pipeline_dry_run_skips_llm_and_email(mocker: MockerFixture) -> None:
    # arrange
    articles = [_make_article(1), _make_article(2)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_email = MagicMock()
    mock_agent = MagicMock()
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
    settings = _make_settings()

    # act
    run_pipeline(settings=settings, dry_run=True)

    # assert
    mock_rss.fetch_recent.assert_called_once_with()
    mock_agent.run.assert_not_called()
    mock_email.send.assert_not_called()


@freeze_time("2026-04-29")
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
            published_at=datetime.fromisoformat(entry["published_at"]),
        )
        for entry in raw["entries"]
    ]
    article_ids = [a.id for a in articles]

    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_agent = MagicMock()
    mock_agent.run.return_value = MagicMock(
        markdown=digest_markdown,
        articles_used=article_ids,
    )
    mock_email = MagicMock()

    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mocker.patch(
        "minizen.core.pipeline.render_email",
        wraps=email_template.render_email,
    )
    settings = _make_settings()

    # act
    run_pipeline(settings=settings)

    # assert
    sent_html = mock_email.send.call_args.kwargs["html"]
    mock_email.send.assert_called_once_with(
        subject="Your Daily Zen — April 29, 2026",
        html=sent_html,
        plain_text=digest_markdown,
    )
    assert all(kw in sent_html for kw in ["Rust", "LLM", "Apple", "Platforms", "Webb"])


@freeze_time("2026-04-29")
def test_pipeline_raises_on_email_failure(mocker: MockerFixture) -> None:
    # arrange
    articles = [_make_article(1)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
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


@freeze_time("2026-04-29")
def test_pipeline_passes_interests_and_avoid_to_agent(
    mocker: MockerFixture,
) -> None:
    # arrange
    articles = [_make_article(1)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_email = MagicMock()
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mock_agent_cls = mocker.patch(
        "minizen.core.pipeline.DigestAgent", return_value=mock_agent
    )
    mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    settings = _make_settings(interests=["Rust", "AI"], avoid=["sports"])

    # act
    run_pipeline(settings=settings)

    # assert
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=2,
        max_words_per_article=500,
        interests=["Rust", "AI"],
        avoid=["sports"],
        preferred_categories=[],
    )


@freeze_time("2026-04-29")
def test_pipeline_passes_preferred_categories_to_agent(
    mocker: MockerFixture,
) -> None:
    # arrange
    articles = [_make_article(1)]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = articles
    mock_email = MagicMock()
    mock_digest_result = MagicMock()
    mock_digest_result.markdown = "## Digest"
    mock_digest_result.articles_used = [1]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_digest_result
    mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
    mock_agent_cls = mocker.patch(
        "minizen.core.pipeline.DigestAgent", return_value=mock_agent
    )
    mocker.patch(
        "minizen.core.pipeline.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    settings = _make_settings(preferred_categories=["Tech", "Science"])

    # act
    run_pipeline(settings=settings)

    # assert
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=2,
        max_words_per_article=500,
        interests=[],
        avoid=[],
        preferred_categories=["Tech", "Science"],
    )
