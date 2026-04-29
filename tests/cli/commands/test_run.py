from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from minizen.cli import app
from minizen.cli.commands.run import _build_settings_from_flags, apply_overrides
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_settings() -> Settings:
    return Settings(
        miniflux=MinifluxConfig(
            url="https://rss.example.com",
            api_key="old-mf-key",
        ),
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="from@example.com",
            to_addr="to@example.com",
            username="user",
            password="pass",
        ),
        ai=AIConfig(),
    )


def test_apply_overrides_replaces_miniflux_api_key() -> None:
    # arrange
    settings = _make_settings()

    # act
    result = apply_overrides(settings=settings, miniflux_api_key="new-mf-key")

    # assert
    assert result.miniflux.api_key == "new-mf-key"
    assert result.miniflux.url == "https://rss.example.com"


def test_apply_overrides_replaces_email_field() -> None:
    # arrange
    settings = _make_settings()

    # act
    result = apply_overrides(settings=settings, smtp_host="smtp.new.com", smtp_port=465)

    # assert
    assert result.email.smtp_host == "smtp.new.com"
    assert result.email.smtp_port == 465
    assert result.email.from_addr == "from@example.com"


def test_apply_overrides_ignores_none_values() -> None:
    # arrange
    settings = _make_settings()

    # act
    result = apply_overrides(settings=settings, miniflux_api_key=None, smtp_host=None)

    # assert
    assert result.miniflux.api_key == "old-mf-key"
    assert result.email.smtp_host == "smtp.example.com"


def test_build_settings_from_flags_succeeds_with_all_required() -> None:
    # act
    result = _build_settings_from_flags(
        miniflux_url=None,
        miniflux_api_key="mf-key",
        model=None,
        top_n=None,
        from_addr="from@example.com",
        to_addr="to@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        email_username="user",
        email_password="pass",
    )

    # assert
    assert result.miniflux.api_key == "mf-key"
    assert result.miniflux.url == "https://reader.miniflux.app"
    assert result.ai.model == "anthropic:claude-haiku-4-5"
    assert result.email.smtp_host == "smtp.example.com"


def test_build_settings_from_flags_exits_when_required_field_missing() -> None:
    # act / assert
    with pytest.raises(typer.Exit):
        _build_settings_from_flags(
            miniflux_url=None,
            miniflux_api_key=None,
            model=None,
            top_n=None,
            from_addr="from@example.com",
            to_addr="to@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            email_username="user",
            email_password="pass",
        )


def test_run_invokes_pipeline(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    mock_settings = MagicMock()
    mock_settings.miniflux.model_copy.return_value = mock_settings.miniflux
    mock_settings.email.model_copy.return_value = mock_settings.email
    mock_settings.ai.model_copy.return_value = mock_settings.ai
    mock_settings.model_copy.return_value = mock_settings
    mock_load = mocker.patch(
        "minizen.cli.commands.run.load_settings", return_value=mock_settings
    )
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    mock_load.assert_called_once_with(config_path=config_path)
    mock_pipeline.assert_called_once_with(settings=mock_settings, dry_run=False)


def test_run_uses_default_config_path(mocker: MockerFixture) -> None:
    # arrange
    mock_settings = MagicMock()
    mock_load = mocker.patch(
        "minizen.cli.commands.run.load_settings", return_value=mock_settings
    )
    mocker.patch("minizen.cli.commands.run.run_pipeline")
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run"])

    # assert
    assert result.exit_code == 0
    expected_default = Path.home() / ".config" / "minizen" / "config.toml"
    mock_load.assert_called_once_with(config_path=expected_default)


def test_run_exits_with_error_on_missing_config(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch(
        "minizen.cli.commands.run.load_settings",
        side_effect=FileNotFoundError("Config not found"),
    )
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run", "--config", "/nonexistent/config.toml"])

    # assert
    assert result.exit_code != 0


def test_run_dry_run_flag_passes_dry_run_to_pipeline(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_settings = MagicMock()
    mock_settings.miniflux.model_copy.return_value = mock_settings.miniflux
    mock_settings.email.model_copy.return_value = mock_settings.email
    mock_settings.ai.model_copy.return_value = mock_settings.ai
    mock_settings.model_copy.return_value = mock_settings
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=mock_settings)
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run", "--dry-run", "--config", str(config_path)])

    # assert
    assert result.exit_code == 0
    mock_pipeline.assert_called_once_with(settings=mock_settings, dry_run=True)


@pytest.mark.parametrize(
    ("exc", "match"),
    [
        (KeyError("MINIFLUX_API_KEY"), "MINIFLUX_API_KEY"),
    ],
)
def test_run_exits_with_error_on_missing_env(
    mocker: MockerFixture, exc: Exception, match: str
) -> None:
    # arrange
    mocker.patch("minizen.cli.commands.run.load_settings", side_effect=exc)
    runner = CliRunner()

    # act
    result = runner.invoke(app, ["run"])

    # assert
    assert result.exit_code != 0
    assert match in result.output


def test_run_flag_overrides_loaded_setting(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_settings = MagicMock()
    mock_settings.miniflux.model_copy.return_value = mock_settings.miniflux
    mock_settings.email.model_copy.return_value = mock_settings.email
    mock_settings.ai.model_copy.return_value = mock_settings.ai
    mock_settings.model_copy.return_value = mock_settings
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=mock_settings)
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["run", "--config", str(config_path), "--miniflux-api-key", "override-key"],
    )

    # assert
    assert result.exit_code == 0
    mock_pipeline.assert_called_once()


def test_run_all_flags_no_config_file(mocker: MockerFixture) -> None:
    # arrange
    mock_pipeline = mocker.patch("minizen.cli.commands.run.run_pipeline")
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        [
            "run",
            "--config",
            "/nonexistent/config.toml",
            "--miniflux-api-key",
            "mf-key",
            "--from-addr",
            "from@example.com",
            "--to-addr",
            "to@example.com",
            "--smtp-host",
            "smtp.example.com",
            "--smtp-port",
            "587",
            "--email-username",
            "user",
            "--email-password",
            "pass",
        ],
    )

    # assert
    assert result.exit_code == 0
    called_settings = mock_pipeline.call_args.kwargs["settings"]
    assert called_settings.miniflux.api_key == "mf-key"
    assert called_settings.email.from_addr == "from@example.com"


def test_run_no_config_file_lists_missing_flags(mocker: MockerFixture) -> None:
    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        app,
        ["run", "--config", "/nonexistent/config.toml"],
    )

    # assert
    assert result.exit_code != 0
    assert "--miniflux-api-key" in result.output
