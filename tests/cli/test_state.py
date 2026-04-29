import logging
from typing import TYPE_CHECKING

from minizen.cli.state import configure_logging

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_configure_logging_sets_debug_level(mocker: MockerFixture) -> None:
    # arrange
    mock_basicconfig = mocker.patch("minizen.cli.state.logging.basicConfig")

    # act
    configure_logging(verbose=True)

    # assert
    mock_basicconfig.assert_called_once_with(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
        force=True,
    )


def test_configure_logging_sets_info_level(mocker: MockerFixture) -> None:
    # arrange
    mock_basicconfig = mocker.patch("minizen.cli.state.logging.basicConfig")

    # act
    configure_logging(verbose=False)

    # assert
    mock_basicconfig.assert_called_once_with(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        force=True,
    )
