import json
from datetime import UTC, datetime
from pathlib import Path

from pytest_mock import MockerFixture

from minizen.config.models import MinifluxConfig
from minizen.providers.rss.miniflux import MinifluxProvider


def test_fetch_unread_returns_articles(mocker: MockerFixture) -> None:
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

    # act
    articles = provider.fetch_unread()

    # assert
    assert len(articles) == 1
    assert articles[0].id == 42
    assert articles[0].title == "Test Article"
    assert articles[0].url == "https://example.com/article"
    assert articles[0].content == "<p>Body</p>"
    assert articles[0].feed_name == "Example Feed"
    assert articles[0].published_at == datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC)
    mock_client_cls.return_value.get_entries.assert_called_once_with(status=["unread"])


def test_fetch_unread_returns_empty_list_when_no_entries(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    mock_client_cls.return_value.get_entries.return_value = {"total": 0, "entries": []}
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    articles = provider.fetch_unread()

    # assert
    assert articles == []


def test_mark_as_read_calls_client_with_ids(mocker: MockerFixture) -> None:
    # arrange
    mock_client_cls = mocker.patch("minizen.providers.rss.miniflux.miniflux.Client")
    config = MinifluxConfig(url="https://rss.example.com", api_key="key")
    provider = MinifluxProvider(config=config)

    # act
    provider.mark_as_read(article_ids=[1, 2, 3])

    # assert
    mock_client_cls.return_value.update_entries.assert_called_once_with(
        entry_ids=[1, 2, 3], status="read"
    )


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


def test_fetch_unread_maps_comments_url_when_present(mocker: MockerFixture) -> None:
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
    articles = provider.fetch_unread()

    # assert
    assert articles[0].comments_url == "https://news.ycombinator.com/item?id=99"


def test_fetch_unread_sets_comments_url_none_when_empty(mocker: MockerFixture) -> None:
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
    articles = provider.fetch_unread()

    # assert
    assert articles[0].comments_url is None


def test_fetch_unread_sets_comments_url_none_when_absent(mocker: MockerFixture) -> None:
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
    articles = provider.fetch_unread()

    # assert
    assert articles[0].comments_url is None


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
    mock_client_cls.return_value.get_entries.assert_called_once_with(status=["unread"])
