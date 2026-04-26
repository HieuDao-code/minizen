"""minizen — A quieter way to stay informed."""

from minizen.ai import DigestAgent, DigestResult
from minizen.config import (
    AIConfig,
    EmailConfig,
    MinifluxConfig,
    Settings,
    load_settings,
)
from minizen.core import run_pipeline
from minizen.providers.email import EmailProvider
from minizen.providers.rss import Article, MinifluxProvider

__version__ = "0.0.0"

__all__ = [
    "AIConfig",
    "Article",
    "DigestAgent",
    "DigestResult",
    "EmailConfig",
    "EmailProvider",
    "MinifluxConfig",
    "MinifluxProvider",
    "Settings",
    "load_settings",
    "run_pipeline",
]
