"""Tests for minizen.config.defaults default constants."""

from pathlib import Path

from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_TOP_N,
)


def test_default_config_path() -> None:
    # act / assert
    assert Path.home() / ".config" / "minizen" / "config.toml" == DEFAULT_CONFIG_PATH


def test_default_miniflux_url() -> None:
    # act / assert
    assert DEFAULT_MINIFLUX_URL == "https://reader.miniflux.app"


def test_default_model() -> None:
    # act / assert
    assert DEFAULT_MODEL == "anthropic:claude-haiku-4-5"


def test_default_top_n() -> None:
    # act / assert
    assert DEFAULT_TOP_N == 10


def test_default_smtp_host() -> None:
    # act / assert
    assert DEFAULT_SMTP_HOST == "smtp.gmail.com"


def test_default_smtp_port() -> None:
    # act / assert
    assert DEFAULT_SMTP_PORT == 587
