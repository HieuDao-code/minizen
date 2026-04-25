import tomllib
from pathlib import Path
from unittest.mock import ANY

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from minizen.cli import app


def test_setup_creates_config_file(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "https://rss.example.com\n"
            "smtp.example.com\n"
            "587\n"
            "from@example.com\n"
            "to@example.com\n"
            "\n"
            "\n"
        ),
    )

    # assert
    assert result.exit_code == 0
    assert config_path.exists()


def test_setup_writes_correct_toml(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "https://rss.example.com\n"
            "smtp.example.com\n"
            "587\n"
            "from@example.com\n"
            "to@example.com\n"
            "\n"
            "\n"
        ),
    )

    # assert
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["miniflux"]["url"] == "https://rss.example.com"
    assert data["email"]["smtp_host"] == "smtp.example.com"
    assert data["email"]["smtp_port"] == 587
    assert data["email"]["from_addr"] == "from@example.com"
    assert data["email"]["to_addr"] == "to@example.com"
    assert data["ai"]["model"] == "anthropic:claude-sonnet-4-6"
    assert data["ai"]["top_n"] == 5


def test_setup_accepts_custom_ai_values(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "https://rss.example.com\n"
            "smtp.example.com\n"
            "587\n"
            "from@example.com\n"
            "to@example.com\n"
            "openai:gpt-4o\n"
            "10\n"
        ),
    )

    # assert
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["ai"]["model"] == "openai:gpt-4o"
    assert data["ai"]["top_n"] == 10


def test_setup_prints_env_reminder(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "https://rss.example.com\n"
            "smtp.example.com\n"
            "587\n"
            "from@example.com\n"
            "to@example.com\n"
            "\n"
            "\n"
        ),
    )

    # assert
    assert "MINIFLUX_API_KEY" in result.output
    assert "EMAIL_USERNAME" in result.output
    assert "EMAIL_PASSWORD" in result.output


def test_setup_creates_parent_directories(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "nested" / "dir" / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "https://rss.example.com\n"
            "smtp.example.com\n"
            "587\n"
            "from@example.com\n"
            "to@example.com\n"
            "\n"
            "\n"
        ),
    )

    # assert
    assert result.exit_code == 0
    assert config_path.exists()


def test_setup_uses_default_config_path(mocker: MockerFixture) -> None:
    # arrange
    mock_write = mocker.patch("minizen.cli.commands.setup.Path.write_bytes")
    mocker.patch("minizen.cli.commands.setup.Path.mkdir")
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup"],
        input=(
            "https://rss.example.com\n"
            "smtp.example.com\n"
            "587\n"
            "from@example.com\n"
            "to@example.com\n"
            "\n"
            "\n"
        ),
    )

    # assert
    mock_write.assert_called_once_with(ANY)
