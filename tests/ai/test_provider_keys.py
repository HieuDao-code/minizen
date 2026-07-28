from typing import TYPE_CHECKING

import pytest

from minizen.ai.provider_keys import resolve_provider_key
from minizen.exceptions import ConfigError, UnsupportedProviderError

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_resolves_anthropic_by_convention() -> None:
    # act
    result = resolve_provider_key(model="anthropic:claude-haiku-4-5")

    # assert
    assert result.prefix == "anthropic"
    assert result.env_var == "ANTHROPIC_API_KEY"
    assert result.label == "Anthropic API key"


def test_resolves_deepseek_without_extra_dependency() -> None:
    # act
    result = resolve_provider_key(model="deepseek:deepseek-chat")

    # assert
    assert result.prefix == "deepseek"
    assert result.env_var == "DEEPSEEK_API_KEY"
    assert result.label == "DeepSeek API key"


def test_resolves_openai_with_display_name_override() -> None:
    # act
    result = resolve_provider_key(model="openai:gpt-4o")

    # assert
    assert result.env_var == "OPENAI_API_KEY"
    assert result.label == "OpenAI API key"


def test_model_name_may_contain_colons() -> None:
    # act
    result = resolve_provider_key(model="openai:ft:gpt-4o:custom")

    # assert
    assert result.prefix == "openai"
    assert result.env_var == "OPENAI_API_KEY"


@pytest.mark.parametrize(
    ("model", "expected_env_var"),
    [
        ("cohere:command-r", "CO_API_KEY"),
        ("huggingface:meta-llama/Llama-3-8B", "HF_TOKEN"),
        ("heroku:claude-3-5-sonnet", "HEROKU_INFERENCE_KEY"),
        ("vercel:anthropic/claude-sonnet-4", "VERCEL_AI_GATEWAY_API_KEY"),
        ("openai-chat:gpt-4o", "OPENAI_API_KEY"),
        ("openai-responses:gpt-4o", "OPENAI_API_KEY"),
    ],
)
def test_override_table_wins_over_convention(
    model: str, expected_env_var: str, mocker: MockerFixture
) -> None:
    # arrange
    mocker.patch("minizen.ai.provider_keys.infer_provider_class")

    # act
    result = resolve_provider_key(model=model)

    # assert
    assert result.env_var == expected_env_var


@pytest.mark.parametrize(
    "model",
    [
        "bedrock:anthropic.claude-3-5-sonnet-20240620-v1:0",
        "azure:gpt-4o",
        "azure-responses:gpt-4o",
        "ollama:llama3",
        "litellm:gpt-4o",
        "google-cloud:gemini-2.0-flash",
    ],
)
def test_unsupported_providers_raise_unsupported_provider_error(model: str) -> None:
    # act / assert
    with pytest.raises(UnsupportedProviderError, match="cannot configure"):
        resolve_provider_key(model=model)


def test_gateway_prefix_is_rejected() -> None:
    # act / assert
    with pytest.raises(UnsupportedProviderError, match="cannot configure"):
        resolve_provider_key(model="gateway/openai:gpt-5")


def test_gateway_prefix_error_names_the_real_env_var() -> None:
    # act / assert
    with pytest.raises(UnsupportedProviderError, match="PYDANTIC_AI_GATEWAY_API_KEY"):
        resolve_provider_key(model="gateway/openai:gpt-5")


def test_unsupported_provider_error_is_catchable_as_config_error() -> None:
    # act / assert
    with pytest.raises(ConfigError):
        resolve_provider_key(model="ollama:llama3")


def test_identifier_without_colon_is_rejected() -> None:
    # act / assert
    with pytest.raises(ConfigError, match="Expected 'provider:model'"):
        resolve_provider_key(model="claude-haiku-4-5")


def test_unknown_prefix_is_rejected() -> None:
    # act / assert
    with pytest.raises(ConfigError, match="Unknown model provider"):
        resolve_provider_key(model="notaprovider:some-model")


def test_missing_sdk_reports_pydantic_ai_install_hint(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch(
        "minizen.ai.provider_keys.infer_provider_class",
        side_effect=ImportError("install the `groq` package — pydantic-ai-slim[groq]"),
    )

    # act / assert
    with pytest.raises(ConfigError, match=r"pydantic-ai-slim\[groq\]"):
        resolve_provider_key(model="groq:llama-3.3-70b")
