import tomllib
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from minizen.cli import app

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from pytest_mock import MockerFixture

_INTERACTIVE_INPUT = (
    "\n"  # model (default: anthropic:claude-haiku-4-5)
    "\n"  # top_n (default: 10)
    "\n"  # smtp host (default: smtp.gmail.com)
    "\n"  # smtp port (default: 587)
    "from@example.com\n"
    "to@example.com\n"
    "email-user\n"
    "email-password\n"
    "miniflux-api-key\n"
    "anthropic-api-key\n"
)


def test_setup_creates_config_file(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
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
        input=_INTERACTIVE_INPUT,
    )

    # assert
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["email"]["smtp_host"] == "smtp.gmail.com"
    assert data["email"]["smtp_port"] == 587
    assert data["email"]["from_addr"] == "from@example.com"
    assert data["email"]["to_addr"] == "to@example.com"
    assert data["ai"]["model"] == "anthropic:claude-haiku-4-5"
    assert data["ai"]["top_n"] == 10


def test_setup_accepts_custom_ai_values(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "openai:gpt-4o\n"
            "10\n"
            "\n"  # smtp host (default)
            "\n"  # smtp port (default)
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "openai-api-key\n"
        ),
    )

    # assert
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["ai"]["model"] == "openai:gpt-4o"
    assert data["ai"]["top_n"] == 10


def test_setup_writes_env_file(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    env_path = tmp_path / ".env"
    assert env_path.exists()
    content = env_path.read_text()
    assert "MINIFLUX_API_KEY=miniflux-api-key" in content
    assert "ANTHROPIC_API_KEY=anthropic-api-key" in content
    assert "MINIZEN_EMAIL_USERNAME=email-user" in content
    assert "MINIZEN_EMAIL_PASSWORD=email-password" in content


def test_setup_creates_parent_directories(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "nested" / "dir" / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    assert result.exit_code == 0
    assert config_path.exists()


def test_setup_non_interactive_writes_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
        ],
    )

    # assert
    assert result.exit_code == 0
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["email"]["from_addr"] == "from@example.com"
    assert data["email"]["to_addr"] == "to@example.com"
    assert data["email"]["smtp_host"] == "smtp.gmail.com"
    assert data["ai"]["model"] == "anthropic:claude-haiku-4-5"


def test_setup_non_interactive_fails_without_from_addr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--to-addr",
            "to@example.com",
        ],
    )

    # assert
    assert result.exit_code != 0


def test_setup_non_interactive_fails_without_to_addr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
        ],
    )

    # assert
    assert result.exit_code != 0


def test_setup_non_interactive_fails_when_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.delenv("MINIFLUX_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MINIZEN_EMAIL_USERNAME", raising=False)
    monkeypatch.delenv("MINIZEN_EMAIL_PASSWORD", raising=False)
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
        ],
    )

    # assert
    assert result.exit_code != 0


def test_setup_writes_openai_key_for_openai_model(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "openai:gpt-4o\n"
            "\n"
            "\n"
            "\n"
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "openai-api-key\n"
        ),
    )

    # assert
    env_path = tmp_path / ".env"
    content = env_path.read_text()
    assert "OPENAI_API_KEY=openai-api-key" in content
    assert "ANTHROPIC_API_KEY" not in content


def test_setup_interactive_exits_on_unknown_model_provider(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "unknown:some-model\n"
            "\n"
            "\n"
            "\n"
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            "email-password\n"
            "miniflux-api-key\n"
            "some-api-key\n"
        ),
    )

    # assert
    assert result.exit_code != 0
    assert "Unknown model provider" in result.output


def test_setup_non_interactive_accepts_openai_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
            "--model",
            "openai:gpt-4o",
        ],
    )

    # assert
    assert result.exit_code == 0


def test_setup_non_interactive_fails_with_unknown_model_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    monkeypatch.setenv("MINIFLUX_API_KEY", "mf-key")
    monkeypatch.setenv("MINIZEN_EMAIL_USERNAME", "user")
    monkeypatch.setenv("MINIZEN_EMAIL_PASSWORD", "pass")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "setup",
            "--no-interactive",
            "--config",
            str(config_path),
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
            "--model",
            "unknown:some-model",
        ],
    )

    # assert
    assert result.exit_code != 0
    assert "Unknown model provider" in result.output


def test_setup_sets_env_file_permissions(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    env_path = tmp_path / ".env"
    assert env_path.stat().st_mode & 0o777 == 0o600


def test_setup_writes_miniflux_section(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["miniflux"]["url"] == "https://reader.miniflux.app"


def test_setup_uses_default_config_path(mocker: MockerFixture) -> None:
    # arrange
    mock_write = mocker.patch("minizen.cli.commands.setup.Path.write_bytes")
    mocker.patch("minizen.cli.commands.setup.Path.mkdir")
    mocker.patch("minizen.cli.commands.setup.Path.write_text")
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup"],
        input=_INTERACTIVE_INPUT,
    )

    # assert
    mock_write.assert_called_once()
