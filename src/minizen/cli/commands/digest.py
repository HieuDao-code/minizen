"""CLI commands to preview or test the digest without sending."""

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from minizen.ai.agent import DigestAgent
from minizen.cli.state import configure_logging
from minizen.config.defaults import DEFAULT_CONFIG_PATH
from minizen.config.loader import load_settings
from minizen.exceptions import MinizenError
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import MinifluxProvider

if TYPE_CHECKING:
    from minizen.config.models import Settings

_CONFIG_OPTION = Annotated[
    Path,
    typer.Option(help="Path to the TOML configuration file.", show_default=True),
]

_VERBOSE_OPTION = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable debug logging."),
]

_DRY_RUN_OPTION = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Fetch articles but skip LLM call and any external sends.",
    ),
]

app = typer.Typer(help="Preview or test the digest pipeline.")


def _load(config: Path) -> Settings:
    """Load settings from a TOML file, exiting with an error message on failure.

    Args:
        config: Path to the TOML configuration file.

    Returns:
        Fully loaded application settings.
    """
    try:
        return load_settings(config_path=config)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)


@app.command("fetch")
def fetch(
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
    verbose: _VERBOSE_OPTION = False,
) -> None:
    """Fetch recent articles and print their titles and URLs."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    try:
        articles = rss.fetch_recent()
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    if not articles:
        typer.echo("No recent articles.")
        return
    typer.echo(f"{len(articles)} recent article(s) in the last 24h:\n")
    for article in articles:
        typer.echo(f"[{article.feed_name}] {article.title}")
        typer.echo(f"  {article.url}")


@app.command("preview")
def preview(
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
    verbose: _VERBOSE_OPTION = False,
    dry_run: _DRY_RUN_OPTION = False,
) -> None:
    """Fetch and summarise articles, then print the Markdown digest."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    try:
        articles = rss.fetch_recent()
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    if not articles:
        typer.echo("No recent articles.")
        return
    if dry_run:
        typer.echo(f"{len(articles)} recent article(s) in the last 24h:\n")
        for article in articles:
            typer.echo(f"[{article.feed_name}] {article.title}")
            typer.echo(f"  {article.url}")
        return
    try:
        agent = DigestAgent(
            model=settings.ai.model,
            top_n=settings.ai.top_n,
            max_words_per_article=settings.ai.max_words_per_article,
        )
        result = agent.run(articles=articles)
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(result.markdown)


@app.command("send-test")
def send_test(
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
    verbose: _VERBOSE_OPTION = False,
    dry_run: _DRY_RUN_OPTION = False,
) -> None:
    """Send a test digest email."""
    configure_logging(verbose=verbose)
    settings = _load(config)
    rss = MinifluxProvider(config=settings.miniflux)
    try:
        articles = rss.fetch_recent()
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    if not articles:
        typer.echo("No recent articles.")
        return
    if dry_run:
        typer.confirm(
            "This will make a real LLM API call but will not send an email. Continue?",
            abort=True,
        )
    try:
        agent = DigestAgent(
            model=settings.ai.model,
            top_n=settings.ai.top_n,
            max_words_per_article=settings.ai.max_words_per_article,
        )
        result = agent.run(articles=articles)
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    selected_ids = set(result.articles_used)
    extra_articles = [a for a in articles if a.id not in selected_ids]
    html, plain_text = render_email(result.markdown, extra_articles=extra_articles)
    if dry_run:
        typer.echo("Dry run — email not sent:\n")
        typer.echo(plain_text)
        return
    today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
    email = EmailProvider(config=settings.email)
    try:
        email.send(
            subject=f"[TEST] Your Daily Zen — {today}",
            html=html,
            plain_text=plain_text,
        )
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo("Test digest sent.")
