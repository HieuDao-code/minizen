"""Tests for the digest CLI subcommands."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import typer
from freezegun import freeze_time
from typer.testing import CliRunner

from minizen.cli import app

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


def _make_settings_mock() -> MagicMock:
    mock = MagicMock()
    mock.ai.model = "anthropic:claude-sonnet-4-6"
    mock.ai.top_n = 5
    mock.ai.max_words_per_article = 500
    return mock


def test_digest_fetch_prints_articles(mocker: MockerFixture) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_article = MagicMock()
    mock_article.feed_name = "Tech Feed"
    mock_article.title = "Article Title"
    mock_article.url = "https://example.com/article"
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = [mock_article]
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "fetch"])

    # assert
    assert result.exit_code == 0
    assert "Tech Feed" in result.output
    assert "Article Title" in result.output
    assert "https://example.com/article" in result.output


def test_digest_fetch_exits_early_when_no_articles(mocker: MockerFixture) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "fetch"])

    # assert
    assert result.exit_code == 0
    assert "No recent articles" in result.output


def test_digest_preview_prints_markdown(mocker: MockerFixture) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_articles = [MagicMock(), MagicMock()]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = mock_articles
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_result = MagicMock()
    mock_result.markdown = "## Today's Digest\n\nSome content."
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_result
    mock_agent_cls = mocker.patch(
        "minizen.cli.commands.digest.DigestAgent", return_value=mock_agent
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "preview"])

    # assert
    assert result.exit_code == 0
    assert "## Today's Digest" in result.output
    mock_agent.run.assert_called_once_with(articles=mock_articles)
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        max_words_per_article=500,
    )


def test_digest_preview_exits_early_when_no_articles(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_agent = MagicMock()
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "preview"])

    # assert
    assert result.exit_code == 0
    assert "No recent articles" in result.output
    mock_agent.run.assert_not_called()


@freeze_time("2026-04-29")
def test_digest_send_test_sends_email(mocker: MockerFixture) -> None:
    # arrange — two articles, one selected, to cover both branches of extra_articles
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    selected = MagicMock()
    unselected = MagicMock()
    mock_articles = [selected, unselected]
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = mock_articles
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_result = MagicMock()
    mock_result.markdown = "## Digest"
    mock_result.articles_used = [selected.id]
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_result
    mock_agent_cls = mocker.patch(
        "minizen.cli.commands.digest.DigestAgent", return_value=mock_agent
    )
    mock_email = MagicMock()
    mocker.patch("minizen.cli.commands.digest.EmailProvider", return_value=mock_email)
    mocker.patch(
        "minizen.cli.commands.digest.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "send-test"])

    # assert
    assert result.exit_code == 0
    mock_email.send.assert_called_once_with(
        subject="[TEST] Your Daily Zen — April 29, 2026",
        html="<h2>Digest</h2>",
        plain_text="## Digest",
    )
    mock_agent_cls.assert_called_once_with(
        model="anthropic:claude-sonnet-4-6",
        top_n=5,
        max_words_per_article=500,
    )


def test_digest_send_test_exits_early_when_no_articles(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_email = MagicMock()
    mocker.patch("minizen.cli.commands.digest.EmailProvider", return_value=mock_email)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "send-test"])

    # assert
    assert result.exit_code == 0
    assert "No recent articles" in result.output
    mock_email.send.assert_not_called()


def test_digest_preview_dry_run_prints_articles_and_skips_llm(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_article = MagicMock()
    mock_article.feed_name = "Tech Feed"
    mock_article.title = "Article Title"
    mock_article.url = "https://example.com/article"
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = [mock_article]
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_agent = MagicMock()
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "preview", "--dry-run"])

    # assert
    assert result.exit_code == 0
    assert "Tech Feed" in result.output
    assert "Article Title" in result.output
    assert "https://example.com/article" in result.output
    mock_agent.run.assert_not_called()


def test_digest_fetch_verbose_calls_configure_logging(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.commands.digest.configure_logging")
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=_make_settings_mock()
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "fetch", "-v"])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


def test_digest_preview_verbose_calls_configure_logging(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.commands.digest.configure_logging")
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=_make_settings_mock()
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "preview", "-v"])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


def test_digest_send_test_verbose_calls_configure_logging(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.commands.digest.configure_logging")
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=_make_settings_mock()
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "send-test", "-v"])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


@pytest.mark.parametrize("subcommand", ["preview", "send-test"])
def test_digest_exits_on_missing_config(mocker: MockerFixture, subcommand: str) -> None:
    # arrange
    mocker.patch(
        "minizen.cli.commands.digest.load_settings",
        side_effect=FileNotFoundError("not found"),
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", subcommand])

    # assert
    assert result.exit_code != 0


@pytest.mark.parametrize("subcommand", ["preview", "send-test"])
def test_digest_exits_on_missing_env(mocker: MockerFixture, subcommand: str) -> None:
    # arrange
    mocker.patch(
        "minizen.cli.commands.digest.load_settings",
        side_effect=KeyError("MINIFLUX_API_KEY"),
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", subcommand])

    # assert
    assert result.exit_code != 0
    assert "MINIFLUX_API_KEY" in result.output


def test_digest_preview_uses_custom_config(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mock_load = mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = []
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "preview", "--config", str(config_path)])

    # assert
    mock_load.assert_called_once_with(config_path=config_path)


def test_digest_send_test_dry_run_shows_confirm_prompt(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = [MagicMock()]
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_confirm = mocker.patch("minizen.cli.commands.digest.typer.confirm")
    mock_agent = MagicMock()
    mock_agent.run.return_value = MagicMock(markdown="## Digest", articles_used=[])
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
    mocker.patch("minizen.cli.commands.digest.EmailProvider", return_value=MagicMock())
    mocker.patch(
        "minizen.cli.commands.digest.render_email",
        return_value=("<h2>Digest</h2>", "## Digest"),
    )
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "send-test", "--dry-run"])

    # assert
    mock_confirm.assert_called_once_with(
        "This will make a real LLM API call but will not send an email. Continue?",
        abort=True,
    )


def test_digest_send_test_dry_run_aborts_when_confirm_declined(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = [MagicMock()]
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mocker.patch("minizen.cli.commands.digest.typer.confirm", side_effect=typer.Abort())
    mock_agent = MagicMock()
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
    runner = CliRunner()

    # act
    runner.invoke(app, ["digest", "send-test", "--dry-run"])

    # assert
    mock_agent.run.assert_not_called()


def test_digest_send_test_dry_run_calls_llm_and_prints_plain_text(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_settings = _make_settings_mock()
    mocker.patch(
        "minizen.cli.commands.digest.load_settings", return_value=mock_settings
    )
    mock_article = MagicMock()
    mock_rss = MagicMock()
    mock_rss.fetch_recent.return_value = [mock_article]
    mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
    mock_confirm = mocker.patch("minizen.cli.commands.digest.typer.confirm")
    mock_result = MagicMock()
    mock_result.markdown = "## Digest"
    mock_result.articles_used = []
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_result
    mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
    mock_email = MagicMock()
    mocker.patch("minizen.cli.commands.digest.EmailProvider", return_value=mock_email)
    mocker.patch(
        "minizen.cli.commands.digest.render_email",
        return_value=("<h2>Digest</h2>", "Plain text digest"),
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["digest", "send-test", "--dry-run"])

    # assert
    assert result.exit_code == 0
    mock_confirm.assert_called_once_with(
        "This will make a real LLM API call but will not send an email. Continue?",
        abort=True,
    )
    mock_agent.run.assert_called_once_with(articles=[mock_article])
    mock_email.send.assert_not_called()
    assert "Dry run — email not sent:" in result.output
    assert "Plain text digest" in result.output
