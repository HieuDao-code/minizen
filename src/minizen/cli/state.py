"""Shared CLI state and logging configuration."""

import logging


def configure_logging(*, verbose: bool) -> None:
    """Configure the root logger for the CLI session.

    Args:
        verbose: When ``True``, sets the root logger to ``DEBUG`` level.
            When ``False``, sets it to ``INFO`` level.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        force=True,
    )
