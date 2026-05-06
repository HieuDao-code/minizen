"""Custom exceptions for minizen error handling."""


class MinizenError(Exception):
    """Base exception for all minizen errors."""


class MinifluxError(MinizenError):
    """Raised when the Miniflux API or network request fails."""


class AIError(MinizenError):
    """Raised when the AI model call fails."""


class EmailError(MinizenError):
    """Raised when the email delivery fails."""
