"""CLI command to run the full fetch-summarise-email pipeline."""

from pathlib import Path
from typing import Annotated, cast

import typer

from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_TOP_N,
)
from minizen.config.loader import load_settings
from minizen.config.models import AIConfig, EmailConfig, MinifluxConfig, Settings
from minizen.core.pipeline import run_pipeline
from minizen.exceptions import MinizenError

_DRY_RUN_OPTION = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Fetch articles but skip LLM call and email send.",
    ),
]


def apply_overrides(
    settings: Settings,
    *,
    miniflux_url: str | None = None,
    miniflux_api_key: str | None = None,
    model: str | None = None,
    top_n: int | None = None,
    from_addr: str | None = None,
    to_addr: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    email_username: str | None = None,
    email_password: str | None = None,
) -> Settings:
    """Return a copy of settings with any non-None flag values applied.

    Args:
        settings: The base settings to override.
        miniflux_url: Override for miniflux.url.
        miniflux_api_key: Override for miniflux.api_key.
        model: Override for ai.model.
        top_n: Override for ai.top_n.
        from_addr: Override for email.from_addr.
        to_addr: Override for email.to_addr.
        smtp_host: Override for email.smtp_host.
        smtp_port: Override for email.smtp_port.
        email_username: Override for email.username.
        email_password: Override for email.password.

    Returns:
        A new Settings instance with overrides applied.
    """
    miniflux_updates = {
        k: v
        for k, v in {"url": miniflux_url, "api_key": miniflux_api_key}.items()
        if v is not None
    }
    ai_updates = {
        k: v for k, v in {"model": model, "top_n": top_n}.items() if v is not None
    }
    email_updates = {
        k: v
        for k, v in {
            "from_addr": from_addr,
            "to_addr": to_addr,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": email_username,
            "password": email_password,
        }.items()
        if v is not None
    }
    return settings.model_copy(
        deep=True,
        update={
            "miniflux": settings.miniflux.model_copy(update=miniflux_updates),
            "ai": settings.ai.model_copy(update=ai_updates),
            "email": settings.email.model_copy(update=email_updates),
        },
    )


def _build_settings_from_flags(
    *,
    miniflux_url: str | None,
    miniflux_api_key: str | None,
    model: str | None,
    top_n: int | None,
    from_addr: str | None,
    to_addr: str | None,
    smtp_host: str | None,
    smtp_port: int | None,
    email_username: str | None,
    email_password: str | None,
) -> Settings:
    """Build a Settings object entirely from CLI flags.

    Args:
        miniflux_url: Miniflux base URL (defaults to hosted instance if None).
        miniflux_api_key: Miniflux API key; required.
        model: AI model identifier (defaults to claude-haiku-4-5 if None).
        top_n: Max articles in digest (defaults to 5 if None).
        from_addr: Sender email address; required.
        to_addr: Recipient email address; required.
        smtp_host: SMTP server hostname; required.
        smtp_port: SMTP server port; required.
        email_username: SMTP login username; required.
        email_password: SMTP login password; required.

    Returns:
        A fully populated Settings instance.

    Raises:
        typer.Exit: With code 1 if any required field is absent.
    """
    required = {
        "--miniflux-api-key": miniflux_api_key,
        "--from-addr": from_addr,
        "--to-addr": to_addr,
        "--smtp-host": smtp_host,
        "--smtp-port": smtp_port,
        "--email-username": email_username,
        "--email-password": email_password,
    }
    missing = [flag for flag, value in required.items() if value is None]
    if missing:
        typer.echo("Config file not found. Required flags:")
        for flag in missing:
            typer.echo(f"  {flag}")
        raise typer.Exit(code=1)

    return Settings(
        miniflux=MinifluxConfig(
            url=miniflux_url or DEFAULT_MINIFLUX_URL,
            api_key=cast("str", miniflux_api_key),
        ),
        email=EmailConfig(
            smtp_host=cast("str", smtp_host),
            smtp_port=cast("int", smtp_port),
            from_addr=cast("str", from_addr),
            to_addr=cast("str", to_addr),
            username=cast("str", email_username),
            password=cast("str", email_password),
        ),
        ai=AIConfig(
            model=model or DEFAULT_MODEL,
            top_n=top_n or DEFAULT_TOP_N,
        ),
    )


def run(
    config: Annotated[
        Path,
        typer.Option(help="Path to the TOML configuration file.", show_default=True),
    ] = DEFAULT_CONFIG_PATH,
    dry_run: _DRY_RUN_OPTION = False,
    miniflux_url: Annotated[
        str | None,
        typer.Option("--miniflux-url", help="Miniflux base URL."),
    ] = None,
    miniflux_api_key: Annotated[
        str | None,
        typer.Option("--miniflux-api-key", help="Miniflux API key."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="AI model identifier."),
    ] = None,
    top_n: Annotated[
        int | None,
        typer.Option("--top-n", help="Number of top articles to include."),
    ] = None,
    from_addr: Annotated[
        str | None,
        typer.Option("--from-addr", help="Sender email address."),
    ] = None,
    to_addr: Annotated[
        str | None,
        typer.Option("--to-addr", help="Recipient email address."),
    ] = None,
    smtp_host: Annotated[
        str | None,
        typer.Option("--smtp-host", help="SMTP server hostname."),
    ] = None,
    smtp_port: Annotated[
        int | None,
        typer.Option("--smtp-port", help="SMTP server port."),
    ] = None,
    email_username: Annotated[
        str | None,
        typer.Option("--email-username", help="SMTP login username."),
    ] = None,
    email_password: Annotated[
        str | None,
        typer.Option("--email-password", help="SMTP login password."),
    ] = None,
) -> None:
    """Run the full digest pipeline: fetch, summarise, and email."""
    _flag_kwargs = {
        "miniflux_url": miniflux_url,
        "miniflux_api_key": miniflux_api_key,
        "model": model,
        "top_n": top_n,
        "from_addr": from_addr,
        "to_addr": to_addr,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "email_username": email_username,
        "email_password": email_password,
    }
    try:
        settings = load_settings(config_path=config)
    except FileNotFoundError:
        settings = _build_settings_from_flags(**_flag_kwargs)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)
    else:
        settings = apply_overrides(settings=settings, **_flag_kwargs)
    try:
        run_pipeline(settings=settings, dry_run=dry_run)
    except MinizenError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
