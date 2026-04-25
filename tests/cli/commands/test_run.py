from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from minizen.cli import app


def test_run_invokes_pipeline(mocker: MockerFixture, tmp_path: Path) -> None:
    # arrange
    mock_settings = MagicMock()
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
    mock_pipeline.assert_called_once_with(settings=mock_settings)


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
