"""Pydantic settings models for the minizen configuration."""

from pathlib import Path  # noqa: TC003

from pydantic import BaseModel, Field, field_validator

from minizen.config.defaults import (
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_TOP_N,
)


class MinifluxConfig(BaseModel):
    """Connection settings for the Miniflux RSS server."""

    url: str = Field(
        default=DEFAULT_MINIFLUX_URL,
        description="Base URL of the Miniflux instance (without /v1/ suffix).",
    )
    api_key: str = Field(description="Miniflux API key for authentication.")


class EmailConfig(BaseModel):
    """SMTP connection and addressing settings for outbound email."""

    smtp_host: str = Field(description="SMTP server hostname.")
    smtp_port: int = Field(description="SMTP server port (typically 587 for STARTTLS).")
    from_addr: str = Field(description="Sender email address.")
    to_addr: str = Field(description="Recipient email address.")
    username: str = Field(description="SMTP login username.")
    password: str = Field(description="SMTP login password or app password.")


class AIConfig(BaseModel):
    """AI model selection and digest size settings."""

    model: str = Field(
        default=DEFAULT_MODEL,
        description="pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-5-5``).",  # noqa: E501
    )
    top_n: int = Field(
        default=DEFAULT_TOP_N,
        description="Maximum number of stories (after deduplication) to include in the digest.",  # noqa: E501
    )
    max_words_per_article: int = Field(
        default=500,
        description="Maximum words of article content sent to the LLM per article.",
    )
    interests: list[str] = Field(
        default_factory=list,
        description="Topics to prioritise when selecting articles.",
    )
    avoid: list[str] = Field(
        default_factory=list,
        description="Topics to avoid when selecting articles.",
    )
    preferred_categories: list[str] = Field(
        default_factory=list,
        description="Miniflux category names to prioritise when selecting articles.",
    )


class QuotesConfig(BaseModel):
    """Location of the favourite-quotes folder used for the digest's closing quote."""

    dir: Path | None = Field(
        default=None,
        description="Directory of one-quote-per-file Markdown notes. Disabled when unset.",  # noqa: E501
    )

    @field_validator("dir")
    @classmethod
    def _expand_user(cls, value: Path | None) -> Path | None:
        """Expand a leading ``~`` so config paths work like shell paths.

        Args:
            value: The configured directory, or ``None`` when disabled.

        Returns:
            The path with ``~`` expanded, or ``None``.
        """
        return value.expanduser() if value is not None else None


class Settings(BaseModel):
    """Top-level application settings composed from all sub-configs."""

    miniflux: MinifluxConfig = Field(description="Miniflux RSS server settings.")
    email: EmailConfig = Field(description="Email delivery settings.")
    ai: AIConfig = Field(description="AI model and digest size settings.")
    quotes: QuotesConfig = Field(
        default_factory=QuotesConfig,
        description="Favourite quote settings.",
    )
