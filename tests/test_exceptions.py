from minizen.exceptions import AIError, EmailError, MinifluxError, MinizenError


def test_minizen_error_is_exception() -> None:
    # act / assert
    assert issubclass(MinizenError, Exception)


def test_miniflux_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(MinifluxError, MinizenError)


def test_ai_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(AIError, MinizenError)


def test_email_error_is_minizen_error() -> None:
    # act / assert
    assert issubclass(EmailError, MinizenError)
