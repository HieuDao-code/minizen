"""Default values for all minizen configuration settings."""

from pathlib import Path

DEFAULT_CONFIG_PATH: Path = Path.home() / ".config" / "minizen" / "config.toml"
DEFAULT_MINIFLUX_URL: str = "https://reader.miniflux.app"
DEFAULT_MODEL: str = "anthropic:claude-haiku-4-5"
DEFAULT_TOP_N: int = 5
DEFAULT_SMTP_HOST: str = "smtp.gmail.com"
DEFAULT_SMTP_PORT: int = 587
