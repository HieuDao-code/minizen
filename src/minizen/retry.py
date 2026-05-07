"""Retry utilities for transient network failures."""

import logging
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

_P = ParamSpec("_P")
_R = TypeVar("_R")


def retry_transient(
    is_transient: Callable[[BaseException], bool],
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Return a tenacity retry decorator for transient network failures.

    Args:
        is_transient: Predicate returning ``True`` if the exception warrants a retry.

    Returns:
        A tenacity ``retry`` decorator configured with: up to 3 attempts,
        exponential backoff with jitter (initial 1 s, max 30 s), a WARNING log
        before each sleep, and reraise of the last exception after exhaustion.
    """
    return retry(  # type: ignore[return-value]
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception(is_transient),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
