from minizen.exceptions import (
    AIError,
    ConfigError,
    EmailError,
    MinifluxError,
    MinizenError,
    UnsupportedProviderError,
)


def test_minizen_error_is_exception() -> None:
    # act / assert
    assert issubclass(MinizenError, Exception)


def test_miniflux_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(MinifluxError, MinizenError)


def test_ai_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(AIError, MinizenError)


def test_email_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(EmailError, MinizenError)


def test_config_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(ConfigError, MinizenError)


def test_unsupported_provider_error_is_config_error() -> None:
    # act / assert
    assert issubclass(UnsupportedProviderError, ConfigError)
