"""Settings loader — reads TOML config and overlays secrets from environment."""

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

from minizen.config.defaults import DEFAULT_MINIFLUX_URL
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def load_settings(*, config_path: Path) -> Settings:
    """Load application settings from a TOML config file and environment variables.

    Reads the TOML file at ``config_path``, then overlays secrets from the
    environment (with ``config_path.parent/.env`` taking precedence over the
    shell environment).

    Args:
        config_path: Path to the TOML configuration file.

    Returns:
        A fully populated ``Settings`` instance.

    Raises:
        FileNotFoundError: If ``config_path`` does not exist.
        KeyError: If a required environment variable is not set.
    """
    load_dotenv(config_path.parent / ".env")
    load_dotenv()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    ai_raw = raw.get("ai", {})

    return Settings(
        miniflux=MinifluxConfig(
            url=raw.get("miniflux", {}).get("url", DEFAULT_MINIFLUX_URL),
            api_key=os.environ["MINIFLUX_API_KEY"],
        ),
        email=EmailConfig(
            smtp_host=raw["email"]["smtp_host"],
            smtp_port=raw["email"]["smtp_port"],
            from_addr=raw["email"]["from_addr"],
            to_addr=raw["email"]["to_addr"],
            username=os.environ["MINIZEN_EMAIL_USERNAME"],
            password=os.environ["MINIZEN_EMAIL_PASSWORD"],
        ),
        ai=AIConfig(**ai_raw),
    )
