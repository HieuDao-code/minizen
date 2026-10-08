from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from typer.testing import CliRunner

from minizen.cli import app

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


def test_root_verbose_flag_calls_configure_logging(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.configure_logging")
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=MagicMock())
    mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    runner.invoke(app, ["-v", "run", "--config", str(config_path)])

    # assert
    mock_configure.assert_called_once_with(verbose=True)


def test_root_no_verbose_flag_calls_configure_logging_false(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    # arrange
    mock_configure = mocker.patch("minizen.cli.configure_logging")
    mocker.patch("minizen.cli.commands.run.load_settings", return_value=MagicMock())
    mocker.patch("minizen.cli.commands.run.run_pipeline")
    config_path = tmp_path / "config.toml"
    config_path.touch()
    runner = CliRunner()

    # act
    runner.invoke(app, ["run", "--config", str(config_path)])

    # assert
    mock_configure.assert_called_once_with(verbose=False)
