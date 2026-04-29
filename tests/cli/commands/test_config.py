import tomllib
from typing import TYPE_CHECKING

import tomli_w
from typer.testing import CliRunner

from minizen.cli import app

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _write_config(path: Path, data: dict) -> None:
    path.write_bytes(tomli_w.dumps(data).encode())


def _minimal_config(path: Path) -> None:
    _write_config(
        path,
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


def test_config_show_prints_config_path(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "show", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    assert str(config_path) in result.output


def test_config_show_prints_key_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "email-pass")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "show", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    assert "https://rss.example.com" in result.output
    assert "smtp.example.com" in result.output


def test_config_validate_succeeds_with_valid_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "email-user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "email-pass")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_config_validate_fails_with_missing_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    monkeypatch.delenv("MINIFLUX_API_KEY", raising=False)
    monkeypatch.setattr("minizen.config.loader.load_dotenv", lambda *_, **__: None)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])

    # assert
    assert result.exit_code != 0


def test_config_set_updates_value(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["config", "set", "ai.top_n", "10", "--config", str(config_path)],
    )

    # assert
    assert result.exit_code == 0
    with config_path.open("rb") as f:
        updated = tomllib.load(f)
    assert updated["ai"]["top_n"] == 10


def test_config_set_string_value(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "ai.model",
            "openai:gpt-4o",
            "--config",
            str(config_path),
        ],
    )

    # assert
    assert result.exit_code == 0
    with config_path.open("rb") as f:
        updated = tomllib.load(f)
    assert updated["ai"]["model"] == "openai:gpt-4o"


def test_config_set_updates_value_in_existing_section(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "miniflux.url",
            "https://new.example.com",
            "--config",
            str(config_path),
        ],
    )

    # assert
    assert result.exit_code == 0
    with config_path.open("rb") as f:
        updated = tomllib.load(f)
    assert updated["miniflux"]["url"] == "https://new.example.com"


def test_config_set_exits_on_invalid_key(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["config", "set", "nonexistent", "value", "--config", str(config_path)],
    )

    # assert
    assert result.exit_code != 0


def test_config_show_exits_on_missing_file(tmp_path: Path) -> None:
    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        app, ["config", "show", "--config", str(tmp_path / "missing.toml")]
    )

    # assert
    assert result.exit_code != 0


def test_config_validate_exits_on_missing_file(tmp_path: Path) -> None:
    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["config", "validate", "--config", str(tmp_path / "missing.toml")],
    )

    # assert
    assert result.exit_code != 0


def test_config_set_exits_on_missing_file(tmp_path: Path) -> None:
    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "ai.top_n",
            "10",
            "--config",
            str(tmp_path / "missing.toml"),
        ],
    )

    # assert
    assert result.exit_code != 0


def test_config_show_displays_ai_defaults_when_section_absent(
    tmp_path: Path,
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    _minimal_config(config_path)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["config", "show", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    assert "anthropic:claude-haiku-4-5" in result.output
    assert "5" in result.output
