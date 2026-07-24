from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from pydantic_ai.exceptions import UnexpectedModelBehavior

from minizen.ai.agent import (
    _SYSTEM_PROMPT,
    DigestAgent,
    DigestResult,
    _build_system_prompt,
    _truncate_words,
)
from minizen.exceptions import AIError
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
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=5)
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
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=3)
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
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=3)
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
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=3)
    articles = [_make_article(article_id=1, comments_url=None)]

    # act
    agent.run(articles=articles)

    # assert
    call_args = mock_agent_cls.return_value.run_sync.call_args
    user_prompt: str = call_args[0][0]
    assert "Comments URL: None" not in user_prompt
    assert "ycombinator" not in user_prompt


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
        model="anthropic:claude-sonnet-5", top_n=3, max_words_per_article=50
    )

    # act
    agent.run(articles=[article])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "word49" in user_prompt
    assert "word50" not in user_prompt


def test_run_raises_ai_error_on_model_failure(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_agent_cls.return_value.run_sync.side_effect = UnexpectedModelBehavior(
        "Model returned empty response"
    )
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=5)
    articles = [_make_article(article_id=1)]

    # act / assert
    with pytest.raises(AIError, match="AI model error"):
        agent.run(articles=articles)


def test_agent_initialized_with_preference_block_when_interests_set(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-5",
        top_n=5,
        interests=["Rust", "AI safety"],
        avoid=[],
    )

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert "Prioritise articles about: Rust, AI safety" in call_kwargs["system_prompt"]


def test_agent_initialized_with_preference_block_when_avoid_set(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-5",
        top_n=5,
        interests=[],
        avoid=["sports", "crypto"],
    )

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert "Avoid articles about: sports, crypto" in call_kwargs["system_prompt"]


def test_agent_uses_base_system_prompt_when_no_preferences(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(model="anthropic:claude-sonnet-5", top_n=5)

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert call_kwargs["system_prompt"] == _SYSTEM_PROMPT


def test_build_system_prompt_includes_preferred_categories_when_set() -> None:
    # act
    result = _build_system_prompt(
        interests=[],
        avoid=[],
        preferred_categories=["Tech", "Science"],
    )

    # assert
    assert (
        "Prefer articles from these Miniflux categories"
        " (in order of preference): Tech, Science"
    ) in result


def test_build_system_prompt_omits_preferred_categories_line_when_empty() -> None:
    # act
    result = _build_system_prompt(interests=[], avoid=[], preferred_categories=[])

    # assert
    assert result == _SYSTEM_PROMPT


def test_run_includes_category_in_prompt_when_present(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=3)
    article = Article(
        id=1,
        title="Test Article",
        url="https://example.com",
        content="<p>Content</p>",
        feed_name="Test Feed",
        category="Tech",
        published_at=datetime(2026, 4, 24, 8, 0, 0, tzinfo=UTC),
    )

    # act
    agent.run(articles=[article])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "Category: Tech" in user_prompt


def test_run_omits_category_in_prompt_when_empty(mocker: MockerFixture) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")
    mock_run_result = mocker.MagicMock()
    mock_run_result.output = DigestResult(markdown="# Digest", articles_used=[1])
    mock_agent_cls.return_value.run_sync.return_value = mock_run_result
    agent = DigestAgent(model="anthropic:claude-sonnet-5", top_n=3)

    # act
    agent.run(articles=[_make_article(article_id=1)])

    # assert
    user_prompt: str = mock_agent_cls.return_value.run_sync.call_args[0][0]
    assert "Category:" not in user_prompt


def test_agent_initialized_with_preference_block_when_preferred_categories_set(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_agent_cls = mocker.patch("minizen.ai.agent.Agent")

    # act
    DigestAgent(
        model="anthropic:claude-sonnet-5",
        top_n=5,
        preferred_categories=["Tech", "Science"],
    )

    # assert
    call_kwargs = mock_agent_cls.call_args.kwargs
    assert (
        "Prefer articles from these Miniflux categories"
        " (in order of preference): Tech, Science"
    ) in call_kwargs["system_prompt"]
