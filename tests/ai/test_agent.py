from datetime import UTC, datetime

from pytest_mock import MockerFixture

from minizen.ai.agent import _SYSTEM_PROMPT, DigestAgent, DigestResult
from minizen.providers.rss.miniflux import Article


def _make_article(*, article_id: int = 1, comments_url: str | None = None) -> Article:
    return Article(
        id=article_id,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
        comments_url=comments_url,
    )


def test_run_returns_digest_result(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(
        markdown="# Digest\n\nSome news.",
        articles_used=[1],
    )
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=5)
    articles = [_make_article(article_id=1)]

    # act
    result = agent.run(articles=articles)

    # assert
    assert result.markdown == "# Digest\n\nSome news."
    assert result.articles_used == [1]
    mock_agent_cls.return_value.run_sync.assert_called_once_with(mocker.ANY)


def test_run_passes_article_data_to_agent(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[42])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=42)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Test Article" in user_prompt
    assert "Test Feed" in user_prompt
    assert "42" in user_prompt


def test_agent_initialized_with_correct_model(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(model="openai:gpt-4o", top_n=3)

    # assert
    mock_agent_cls.assert_called_once_with(
        model="openai:gpt-4o",
        output_type=DigestResult,
        system_prompt=_SYSTEM_PROMPT,
    )


def test_run_includes_comments_url_in_prompt_when_present(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [
        _make_article(
            article_id=1, comments_url="https://news.ycombinator.com/item?id=99"
        )
    ]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "https://news.ycombinator.com/item?id=99" in user_prompt


def test_run_omits_comments_url_in_prompt_when_none(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-4-6", top_n=3)
    articles = [_make_article(article_id=1, comments_url=None)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Comments URL: None" not in user_prompt
    assert "ycombinator" not in user_prompt
