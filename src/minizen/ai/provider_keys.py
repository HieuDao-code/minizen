"""Map a pydantic-ai model identifier to the API key its provider requires."""

from typing import NamedTuple

from pydantic_ai.providers import infer_provider_class

from minizen.exceptions import ConfigError, UnsupportedProviderError

_KEY_ENV_OVERRIDES: dict[str, str] = {
    "cohere": "CO_API_KEY",
    "heroku": "HEROKU_INFERENCE_KEY",
    "huggingface": "HF_TOKEN",
    "openai-chat": "OPENAI_API_KEY",
    "openai-responses": "OPENAI_API_KEY",
    "vercel": "VERCEL_AI_GATEWAY_API_KEY",
    "voyageai": "VOYAGE_API_KEY",
}

_DISPLAY_NAMES: dict[str, str] = {
    "deepseek": "DeepSeek",
    "github": "GitHub",
    "huggingface": "Hugging Face",
    "moonshotai": "Moonshot AI",
    "openai": "OpenAI",
    "openai-chat": "OpenAI",
    "openai-responses": "OpenAI",
    "openrouter": "OpenRouter",
    "ovhcloud": "OVHcloud",
    "sambanova": "SambaNova",
    "voyageai": "Voyage AI",
    "xai": "xAI",
    "zai": "Z.ai",
}

_UNSUPPORTED_PREFIXES: frozenset[str] = frozenset(
    {
        "azure",
        "azure-responses",
        "bedrock",
        "google-cloud",
        "litellm",
        "ollama",
    }
)


class ProviderKey(NamedTuple):
    """The API key requirement for a model identifier's provider."""

    prefix: str
    label: str
    env_var: str


def resolve_provider_key(*, model: str) -> ProviderKey:
    """Resolve which API key the provider in *model* requires.

    Validates the provider prefix against pydantic-ai's own registry, so
    minizen never maintains a provider list of its own.

    Args:
        model: pydantic-ai model identifier, e.g. ``deepseek:deepseek-chat``.

    Returns:
        A ``ProviderKey`` naming the provider, its prompt label, and the
        environment variable holding its API key.

    Raises:
        UnsupportedProviderError: If the provider is valid but needs more than
            a single API key, so the setup wizard cannot configure it.
        ConfigError: If *model* has no ``provider:`` prefix, the prefix is not a
            known provider, or the provider's SDK is not installed.
    """
    if ":" not in model:
        msg = (
            f"Invalid model identifier: {model!r}. "
            "Expected 'provider:model', for example 'deepseek:deepseek-chat'."
        )
        raise ConfigError(msg)

    prefix = model.split(":", maxsplit=1)[0]

    if prefix in _UNSUPPORTED_PREFIXES:
        msg = (
            f"The setup wizard cannot configure the {prefix!r} provider, which "
            "needs more than a single API key. Set its environment variables "
            "yourself and edit ai.model directly."
        )
        raise UnsupportedProviderError(msg)

    try:
        infer_provider_class(prefix)
    except ValueError as exc:
        msg = f"Unknown model provider: {prefix!r}."
        raise ConfigError(msg) from exc
    except ImportError as exc:
        msg = f"Provider {prefix!r} needs an extra package. {exc}"
        raise ConfigError(msg) from exc

    env_var = _KEY_ENV_OVERRIDES.get(
        prefix, f"{prefix.upper().replace('-', '_')}_API_KEY"
    )
    display = _DISPLAY_NAMES.get(prefix, prefix.replace("-", " ").title())
    return ProviderKey(prefix=prefix, label=f"{display} API key", env_var=env_var)
