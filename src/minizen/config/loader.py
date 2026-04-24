import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings


def load_settings(*, config_path: Path) -> Settings:
    load_dotenv()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    ai_raw = raw.get("ai", {})

    return Settings(
        miniflux=MinifluxConfig(
            url=raw["miniflux"]["url"],
            api_key=os.environ["MINIFLUX_API_KEY"],
        ),
        email=EmailConfig(
            smtp_host=raw["email"]["smtp_host"],
            smtp_port=raw["email"]["smtp_port"],
            from_addr=raw["email"]["from_addr"],
            to_addr=raw["email"]["to_addr"],
            username=os.environ["EMAIL_USERNAME"],
            password=os.environ["EMAIL_PASSWORD"],
        ),
        ai=AIConfig(
            model=ai_raw.get("model", "anthropic:claude-sonnet-4-6"),
            top_n=ai_raw.get("top_n", 5),
        ),
    )
