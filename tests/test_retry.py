"""Tests for the retry_transient decorator factory."""

from typing import TYPE_CHECKING

import pytest

from minizen.retry import retry_transient

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_retry_transient_returns_value_on_first_success() -> None:
    @retry_transient(lambda _: True)
    def fn() -> str:
        return "ok"

    assert fn() == "ok"


def test_retry_transient_retries_on_transient_error(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("time.sleep")
    call_count = 0

    @retry_transient(lambda exc: isinstance(exc, ValueError))
    def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            msg = "transient"
            raise ValueError(msg)
        return "ok"

    # act
    result = fn()

    # assert
    assert result == "ok"
    assert call_count == 3


def test_retry_transient_does_not_retry_permanent_error(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("time.sleep")
    call_count = 0

    @retry_transient(lambda exc: isinstance(exc, ValueError))
    def fn() -> None:
        nonlocal call_count
        call_count += 1
        msg = "permanent"
        raise TypeError(msg)

    # act / assert
    with pytest.raises(TypeError, match="permanent"):
        fn()
    assert call_count == 1


def test_retry_transient_reraises_after_exhaustion(mocker: MockerFixture) -> None:
    # arrange
    mocker.patch("time.sleep")
    call_count = 0

    @retry_transient(lambda exc: isinstance(exc, ValueError))
    def fn() -> None:
        nonlocal call_count
        call_count += 1
        msg = "transient"
        raise ValueError(msg)

    # act / assert
    with pytest.raises(ValueError, match="transient"):
        fn()
    assert call_count == 3
