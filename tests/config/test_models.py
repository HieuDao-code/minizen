import pytest
from pydantic import ValidationError

from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def test_miniflux_config_accepts_valid_values() -> None:
    # act
    config = MinifluxConfig(url="https://rss.example.com", api_key="key123")

    # assert
    assert config.url == "https://rss.example.com"
    assert config.api_key == "key123"


def test_email_config_accepts_valid_values() -> None:
    # act
    config = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        from_addr="from@example.com",
        to_addr="to@example.com",
        username="user",
        password="pass",
    )

    # assert
    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.from_addr == "from@example.com"
    assert config.to_addr == "to@example.com"
    assert config.username == "user"
    assert config.password == "pass"


def test_ai_config_defaults() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.model == "anthropic:claude-haiku-4-5"
    assert config.top_n == 10


def test_ai_config_accepts_custom_values() -> None:
    # act
    config = AIConfig(model="openai:gpt-4o", top_n=3)

    # assert
    assert config.model == "openai:gpt-4o"
    assert config.top_n == 3


def test_settings_composes_sub_configs() -> None:
    # arrange
    miniflux = MinifluxConfig(url="https://rss.example.com", api_key="key")
    email = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="a@example.com",
        to_addr="b@example.com",
        username="user",
        password="pass",
    )
    ai = AIConfig()

    # act
    settings = Settings(miniflux=miniflux, email=email, ai=ai)

    # assert
    assert settings.miniflux.url == "https://rss.example.com"
    assert settings.email.smtp_host == "smtp.example.com"
    assert settings.ai.top_n == 10


def test_settings_requires_miniflux() -> None:
    # act / assert
    with pytest.raises(ValidationError):
        Settings.model_validate({"email": {}, "ai": {}})


def test_ai_config_default_max_words_per_article() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.max_words_per_article == 500


def test_ai_config_accepts_custom_max_words_per_article() -> None:
    # act
    config = AIConfig(max_words_per_article=300)

    # assert
    assert config.max_words_per_article == 300


def test_ai_config_defaults_interests_and_avoid_to_empty_lists() -> None:
    # act
    config = AIConfig()

    # assert
    assert config.interests == []
    assert config.avoid == []


def test_ai_config_accepts_interests_and_avoid() -> None:
    # act
    config = AIConfig(
        interests=["Rust", "AI safety"],
        avoid=["sports", "crypto"],
    )

    # assert
    assert config.interests == ["Rust", "AI safety"]
    assert config.avoid == ["sports", "crypto"]
