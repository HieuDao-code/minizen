"""Tests for the Miniflux RSS provider."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import miniflux
import pytest
from freezegun import freeze_time

from minizen.config.models import MinifluxConfig
from minizen.exceptions import MinifluxError
from minizen.providers.rss.miniflux import MinifluxProvider, is_transient_miniflux

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_returns_articles(mocker: MockerFixture) -> None:
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
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)
    expected_ts = int(
        (datetime(2026, 5, 4, 10, 0, 0, tzinfo=UTC) - timedelta(hours=24)).timestamp()
    )

    # act
    articles = provider.fetch_recent()

    # assert
    assert len(articles) == 1
    assert articles[0].id == 42
    assert articles[0].title == "Test Article"
    assert articles[0].url == "https://example.com/article"
    assert articles[0].content == "<p>Body</p>"
    assert articles[0].feed_name == "Example Feed"
    assert articles[0].published_at == datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC)
    mock_client_cls.return_value.get_entries.assert_called_once_with(
        published_after=expected_ts
    )


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_returns_empty_list_when_no_entries(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {"total": 0, "entries": []}
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles == []


def test_miniflux_client_initialized_with_config(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    config = MinifluxConfig(url="https://rss.example.com", api_key="secret-key")

    # act
    MinifluxProvider(config=config)

    # assert
    mock_client_cls.assert_called_once_with(
        base_url="https://rss.example.com", api_key="secret-key"
    )


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_maps_comments_url_when_present(mocker: MockerFixture) -> None:
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
    articles = provider.fetch_recent()

    # assert
    assert articles[0].comments_url == "https://news.ycombinator.com/item?id=99"


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_sets_comments_url_none_when_empty(mocker: MockerFixture) -> None:
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
    articles = provider.fetch_recent()

    # assert
    assert articles[0].comments_url is None


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_sets_comments_url_none_when_absent(mocker: MockerFixture) -> None:
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
    articles = provider.fetch_recent()

    # assert
    assert articles[0].comments_url is None


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_with_fixture_data(mocker: MockerFixture) -> None:
    # arrange
    fixture_path = Path(__file__).parents[2] / "fixtures" / "miniflux_response.json"
    fixture = json.loads(fixture_path.read_text())
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = fixture
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)
    expected_ts = int(
        (datetime(2026, 5, 4, 10, 0, 0, tzinfo=UTC) - timedelta(hours=24)).timestamp()
    )

    # act
    articles = provider.fetch_recent()

    # assert
    assert len(articles) == 5
    feed_names = {a.feed_name for a in articles}
    assert feed_names == {"Hacker News", "The Verge", "Ars Technica"}
    assert all(a.title for a in articles)
    assert all(a.url for a in articles)
    assert all(a.published_at.tzinfo is UTC for a in articles)
    mock_client_cls.return_value.get_entries.assert_called_once_with(
        published_after=expected_ts
    )


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_on_client_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_response = mocker.MagicMock()
    mock_response.status_code = 403
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error_message": "Forbidden"}
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = miniflux.ClientError(
        mock_response
    )
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_on_os_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = OSError("Connection refused")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()


def test_is_transient_miniflux_returns_true_for_os_error() -> None:
    assert is_transient_miniflux(exc=OSError("timeout")) is True


def test_is_transient_miniflux_returns_true_for_5xx_client_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_response = mocker.MagicMock()
    mock_response.status_code = 503

    # act / assert
    assert is_transient_miniflux(exc=miniflux.ClientError(mock_response)) is True


def test_is_transient_miniflux_returns_false_for_4xx_client_error(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_response = mocker.MagicMock()
    mock_response.status_code = 403

    # act / assert
    assert is_transient_miniflux(exc=miniflux.ClientError(mock_response)) is False


def test_is_transient_miniflux_returns_false_for_other_exceptions() -> None:
    assert is_transient_miniflux(exc=ValueError("unrelated")) is False


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_retries_on_transient_error_then_succeeds(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    call_count = 0

    def flaky_get_entries(**_: object) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            msg = "timeout"
            raise OSError(msg)
        return {"total": 0, "entries": []}

    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = flaky_get_entries
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles == []
    assert call_count == 2


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_miniflux_error_after_exhausting_retries(
    mocker: MockerFixture,
) -> None:
    # arrange
    mocker.patch("tenacity.nap.sleep")
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = OSError("timeout")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(MinifluxError, match="Miniflux API error"):
        provider.fetch_recent()
    assert mock_client_cls.return_value.get_entries.call_count == 3


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_extracts_category_from_entry(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 1,
                "title": "Test",
                "url": "https://example.com",
                "content": "<p>Body</p>",
                "feed": {"title": "Hacker News", "category": {"title": "Tech"}},
                "published_at": "2026-05-04T08:00:00Z",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles[0].category == "Tech"


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_defaults_category_to_empty_string_when_absent(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {
        "total": 1,
        "entries": [
            {
                "id": 1,
                "title": "Test",
                "url": "https://example.com",
                "content": "<p>Body</p>",
                "feed": {"title": "Hacker News"},
                "published_at": "2026-05-04T08:00:00Z",
            }
        ],
    }
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles[0].category == ""
