"""Tests for the Miniflux RSS provider."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import miniflux
import pytest
from freezegun import freeze_time

from minizen.config.models import MinifluxConfig
from minizen.providers.rss.miniflux import MinifluxProvider

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


def _make_miniflux_error_response(mocker: MockerFixture, status_code: int) -> object:
    mock_response = mocker.MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {"Content-Type": "text/plain"}
    return mock_response


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_on_unauthorized(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    response = _make_miniflux_error_response(mocker, status_code=401)
    mock_client_cls.return_value.get_entries.side_effect = miniflux.AccessUnauthorized(
        response
    )
    config = MinifluxConfig(url="https://rss.example.com", api_key="bad-key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(miniflux.AccessUnauthorized):
        provider.fetch_recent()


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_on_rate_limit(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    response = _make_miniflux_error_response(mocker, status_code=429)
    mock_client_cls.return_value.get_entries.side_effect = miniflux.ClientError(response)
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(miniflux.ClientError) as exc_info:
        provider.fetch_recent()
    assert exc_info.value.status_code == 429


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_on_server_error(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    response = _make_miniflux_error_response(mocker, status_code=500)
    mock_client_cls.return_value.get_entries.side_effect = miniflux.ServerError(response)
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(miniflux.ServerError):
        provider.fetch_recent()


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_raises_on_connection_error(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.side_effect = OSError("Connection refused")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act / assert
    with pytest.raises(OSError, match="Connection refused"):
        provider.fetch_recent()


@freeze_time("2026-05-04T10:00:00Z")
def test_fetch_recent_returns_empty_when_entries_key_missing(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {"total": 0}
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_recent()

    # assert
    assert articles == []


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
