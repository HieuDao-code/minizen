"""Tests that all public symbols are importable from their declared locations."""

import minizen
from minizen import (
    AIConfig,
    AIError,
    Article,
    ConfigError,
    DigestAgent,
    DigestResult,
    EmailConfig,
    EmailError,
    EmailProvider,
    MinifluxConfig,
    MinifluxError,
    MinifluxProvider,
    MinizenError,
    Settings,
    UnsupportedProviderError,
    load_settings,
    run_pipeline,
)
from minizen.ai import (
    DigestAgent as _DigestAgent,
    DigestResult as _DigestResult,
)
from minizen.config import (
    AIConfig as _AIConfig,
    EmailConfig as _EmailConfig,
    MinifluxConfig as _MinifluxConfig,
    Settings as _Settings,
    load_settings as _load_settings,
)
from minizen.core import run_pipeline as _run_pipeline
from minizen.exceptions import (
    AIError as _AIError,
    ConfigError as _ConfigError,
    EmailError as _EmailError,
    MinifluxError as _MinifluxError,
    MinizenError as _MinizenError,
    UnsupportedProviderError as _UnsupportedProviderError,
)
from minizen.providers.email import EmailProvider as _EmailProvider
from minizen.providers.rss import (
    Article as _Article,
    MinifluxProvider as _MinifluxProvider,
)


def test_top_level_all() -> None:
    # arrange
    expected = {
        "AIConfig",
        "AIError",
        "Article",
        "ConfigError",
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
        "UnsupportedProviderError",
        "load_settings",
        "run_pipeline",
    }

    # act / assert
    assert set(minizen.__all__) == expected


def test_top_level_imports_are_same_objects() -> None:
    # assert
    assert run_pipeline is _run_pipeline
    assert load_settings is _load_settings
    assert Settings is _Settings
    assert AIConfig is _AIConfig
    assert EmailConfig is _EmailConfig
    assert MinifluxConfig is _MinifluxConfig
    assert EmailProvider is _EmailProvider
    assert Article is _Article
    assert MinifluxProvider is _MinifluxProvider
    assert DigestAgent is _DigestAgent
    assert DigestResult is _DigestResult


def test_exception_imports_are_same_objects() -> None:
    # assert
    assert MinizenError is _MinizenError
    assert MinifluxError is _MinifluxError
    assert AIError is _AIError
    assert EmailError is _EmailError
    assert ConfigError is _ConfigError
    assert UnsupportedProviderError is _UnsupportedProviderError
