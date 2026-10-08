# Copyright (c) 2026 HieuDao-code
# SPDX-License-Identifier: MIT
"""Default values for all minizen configuration settings."""

from pathlib import Path

DEFAULT_CONFIG_PATH: Path = Path.home() / ".config" / "minizen" / "config.toml"
DEFAULT_MINIFLUX_URL: str = "https://reader.miniflux.app"
DEFAULT_MODEL: str = "anthropic:claude-haiku-5-5"
DEFAULT_TOP_N: int = 10
DEFAULT_SMTP_HOST: str = "smtp.gmail.com"
DEFAULT_SMTP_PORT: int = 587
