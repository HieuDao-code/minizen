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
from minizen.exceptions import AIError, EmailError, MinifluxError, MinizenError
from minizen.providers.email import EmailProvider
from minizen.providers.rss import Article, MinifluxProvider

__version__ = "0.6.2"

__all__ = [
    "AIConfig",
    "AIError",
    "Article",
    "DigestAgent",
    "DigestResult",
    "EmailConfig",
    "EmailError",
    "EmailProvider",
    "MinifluxConfig",
    "MinifluxError",
    "MinifluxProvider",
    "MinizenError",
    "Settings",
    "load_settings",
    "run_pipeline",
]
