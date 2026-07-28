"""Custom exceptions for minizen error handling."""


class MinizenError(Exception):
    """Base exception for all minizen errors."""


class MinifluxError(MinizenError):
    """Raised when the Miniflux API or network request fails."""


class AIError(MinizenError):
    """Raised when the AI model call fails."""


class EmailError(MinizenError):
    """Raised when the email delivery fails."""


class ConfigError(MinizenError):
    """Raised when the configuration is invalid or incomplete."""


class UnsupportedProviderError(ConfigError):
    """Raised for a valid provider the setup wizard cannot configure.

    These providers (for example ``bedrock`` and ``ollama``) need AWS
    credentials or a base URL rather than a single API key. They still work at
    run time when the user configures the environment themselves, so callers
    should treat this as informational rather than as a failure.
    """
