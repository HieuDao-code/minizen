from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UnexpectedModelBehavior

from minizen.ai.agent import _SYSTEM_PROMPT, DigestAgent, DigestResult, _truncate_words
from minizen.providers.rss.miniflux import Article

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


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


# --- error handling ---


def test_run_raises_on_model_http_error(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_agent_cls.return_value.run_sync.side_effect = ModelHTTPError(
        status_code=429, model_name="anthropic:claude-haiku-4-5"
    )
    agent = DigestAgent(model="anthropic:claude-haiku-4-5", top_n=3)
    articles = [_make_article(article_id=1)]

    # act / assert
    with pytest.raises(ModelHTTPError) as exc_info:
        agent.run(articles=articles)
    assert exc_info.value.status_code == 429


def test_run_raises_on_unexpected_model_behavior(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_agent_cls.return_value.run_sync.side_effect = UnexpectedModelBehavior(
        "Model returned empty response"
    )
    agent = DigestAgent(model="anthropic:claude-haiku-4-5", top_n=3)
    articles = [_make_article(article_id=1)]

    # act / assert
    with pytest.raises(UnexpectedModelBehavior, match="Model returned empty response"):
        agent.run(articles=articles)


def test_run_raises_on_agent_run_error(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_agent_cls.return_value.run_sync.side_effect = AgentRunError("Agent run failed")
    agent = DigestAgent(model="anthropic:claude-haiku-4-5", top_n=3)
    articles = [_make_article(article_id=1)]

    # act / assert
    with pytest.raises(AgentRunError, match="Agent run failed"):
        agent.run(articles=articles)


# --- _truncate_words ---


def test_truncate_words_strips_html_tags() -> None:
    # act
    result = _truncate_words(html="<p>Hello world</p>", max_words=10)

    # assert
    assert "<p>" not in result
    assert "Hello" in result
    assert "world" in result


def test_truncate_words_truncates_at_exact_word_count() -> None:
    # arrange
    html = "<p>" + " ".join(f"word{i}" for i in range(100)) + "</p>"

    # act
    result = _truncate_words(html=html, max_words=5)

    # assert
    assert result.split() == ["word0", "word1", "word2", "word3", "word4"]


def test_truncate_words_preserves_all_words_when_under_limit() -> None:
    # act
    result = _truncate_words(html="<p>one two three</p>", max_words=10)

    # assert
    assert result.split() == ["one", "two", "three"]


# --- max_words_per_article wiring ---


def test_run_truncates_content_at_max_words(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    long_content = "<p>" + " ".join(f"word{i}" for i in range(200)) + "</p>"
    article = Article(
        id=1,
        title="Test",
        url="https://example.com",
        content=long_content,
        feed_name="Feed",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
    )
    agent = DigestAgent(
        model="anthropic:claude-sonnet-4-6", top_n=3, max_words_per_article=50
    )

    # act
    agent.run(articles=[article])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "word49" in user_prompt
    assert "word50" not in user_prompt
