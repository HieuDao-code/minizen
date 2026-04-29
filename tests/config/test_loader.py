from typing import TYPE_CHECKING

import pytest
import tomli_w

from minizen.config.loader import load_settings

if TYPE_CHECKING:
    from pathlib import Path


def _write_config(path: Path, data: dict) -> None:
    path.write_bytes(tomli_w.dumps(data).encode())


def test_load_settings_reads_toml_and_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
            "ai": {"model": "anthropic:claude-sonnet-4-6", "top_n": 10},
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "email-pass")
    # act
    settings = load_settings(config_path=config_file)

    # assert
    assert settings.miniflux.url == "https://rss.example.com"
    assert settings.miniflux.api_key == "mf-key"
    assert settings.email.smtp_host == "smtp.example.com"
    assert settings.email.smtp_port == 587
    assert settings.email.username == "email-user"
    assert settings.email.password == "email-pass"
    assert settings.ai.model == "anthropic:claude-sonnet-4-6"
    assert settings.ai.top_n == 10


def test_load_settings_uses_ai_defaults_when_section_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "email-pass")

    # act
    settings = load_settings(config_path=config_file)

    # assert
    assert settings.ai.model == "anthropic:claude-haiku-4-5"
    assert settings.ai.top_n == 10


def test_load_settings_raises_when_env_var_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "miniflux": {"url": "https://rss.example.com"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        },
    )
    monkeypatch.delenv("MINIFLUX_API_KEY", raising=False)
    monkeypatch.setattr("minizen.config.loader.load_dotenv", lambda *_, **__: None)

    # act / assert
    with pytest.raises(KeyError, match="MINIFLUX_API_KEY"):
        load_settings(config_path=config_file)


def test_load_settings_raises_when_config_file_missing(tmp_path: Path) -> None:
    # act / assert
    with pytest.raises(FileNotFoundError):
        load_settings(config_path=tmp_path / "missing.toml")


def test_load_settings_uses_default_miniflux_url_when_section_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    config_file = tmp_path / "config.toml"
    _write_config(
        config_file,
        {
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        },
    )
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "email-pass")

    # act
    settings = load_settings(config_path=config_file)

    # assert
    assert settings.miniflux.url == "https://reader.miniflux.app"
    assert settings.miniflux.api_key == "mf-key"
