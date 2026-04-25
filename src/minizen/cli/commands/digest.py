from pathlib import Path
from typing import Annotated, cast

import mistune
import typer

from minizen.ai.agent import DigestAgent
from minizen.config.loader import load_settings
from minizen.config.models import Settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.rss.miniflux import MinifluxProvider

_DEFAULT_CONFIG = Path.home() / ".config" / "minizen" / "config.toml"

_CONFIG_OPTION = Annotated[
    Path,
    typer.Option(help="Path to the TOML configuration file.", show_default=True),
]

app = typer.Typer(help="Preview or test the digest without marking articles as read.")


def _load(config: Path) -> Settings:
    try:
        return load_settings(config_path=config)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)


@app.command("preview")
def preview(config: _CONFIG_OPTION = _DEFAULT_CONFIG) -> None:
    """Fetch and summarise articles, then print the Markdown digest."""
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    typer.echo(result.markdown)


@app.command("send-test")
def send_test(config: _CONFIG_OPTION = _DEFAULT_CONFIG) -> None:
    """Send a test digest email without marking articles as read."""
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        typer.echo("No unread articles.")
        return
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    html = cast(str, mistune.html(result.markdown))
    email = EmailProvider(config=settings.email)
    email.send(subject="[TEST] Your Daily Digest", html=html)
    typer.echo("Test digest sent.")
