"""Interactive and non-interactive setup wizard for minizen."""

import os
from pathlib import Path
from typing import Annotated

import tomli_w
import typer

from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_TOP_N,
)


def _provider_key_info(model: str) -> tuple[str, str]:
    """Return the prompt label and env var name for the AI provider API key.

    Args:
        model: pydantic-ai model identifier (e.g. ``anthropic:claude-haiku-4-5``).

    Returns:
        A tuple of (prompt_label, env_var_name).

    Raises:
        typer.Exit: If the model prefix is not a recognised provider.
    """
    if model.startswith("anthropic:"):
        return "Anthropic API key", "ANTHROPIC_API_KEY"
    if model.startswith("openai:"):
        return "OpenAI API key", "OPENAI_API_KEY"
    prefix = model.split(":", maxsplit=1)[0] if ":" in model else model
    typer.echo(f"Error: Unknown model provider: {prefix}")
    raise typer.Exit(code=1)


def setup(
    config: Annotated[
        Path,
        typer.Option(help="Path to write the TOML configuration file."),
    ] = DEFAULT_CONFIG_PATH,
    no_interactive: Annotated[
        bool,
        typer.Option(
            "--no-interactive", help="Skip prompts; read secrets from env vars."
        ),
    ] = False,
    from_addr: Annotated[
        str | None,
        typer.Option("--from-addr", help="From email address."),
    ] = None,
    to_addr: Annotated[
        str | None,
        typer.Option("--to-addr", help="To email address."),
    ] = None,
    smtp_host: Annotated[
        str | None,
        typer.Option("--smtp-host", help="SMTP host."),
    ] = None,
    smtp_port: Annotated[
        int | None,
        typer.Option("--smtp-port", help="SMTP port."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="AI model identifier."),
    ] = None,
    top_n: Annotated[
        int | None,
        typer.Option("--top-n", help="Number of top articles to include."),
    ] = None,
) -> None:
    """Interactive wizard to create a minizen configuration file."""
    if no_interactive:
        _setup_non_interactive(
            config=config,
            from_addr=from_addr,
            to_addr=to_addr,
            smtp_host=smtp_host or DEFAULT_SMTP_HOST,
            smtp_port=smtp_port or DEFAULT_SMTP_PORT,
            model=model or DEFAULT_MODEL,
            top_n=top_n or DEFAULT_TOP_N,
        )
    else:
        _setup_interactive(
            config=config,
            from_addr=from_addr,
            to_addr=to_addr,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            model=model,
            top_n=top_n,
        )


def _setup_non_interactive(
    *,
    config: Path,
    from_addr: str | None,
    to_addr: str | None,
    smtp_host: str,
    smtp_port: int,
    model: str,
    top_n: int,
) -> None:
    """Write config non-interactively, reading secrets from environment variables.

    Args:
        config: Destination path for the TOML config file.
        from_addr: Sender email address; required, exits with code 1 if absent.
        to_addr: Recipient email address; required, exits with code 1 if absent.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        model: AI model identifier.
        top_n: Number of top articles to include in the digest.
    """
    if not from_addr:
        typer.echo("Error: --from-addr is required in non-interactive mode.")
        raise typer.Exit(code=1)
    if not to_addr:
        typer.echo("Error: --to-addr is required in non-interactive mode.")
        raise typer.Exit(code=1)

    _, ai_key_var = _provider_key_info(model)

    for var in (
        "MINIFLUX_API_KEY",
        ai_key_var,
        "MINIZEN_EMAIL_USERNAME",
        "MINIZEN_EMAIL_PASSWORD",
    ):
        if not os.environ.get(var):
            typer.echo(f"Error: environment variable {var} is not set.")
            raise typer.Exit(code=1)

    _write_config(
        config=config,
        from_addr=from_addr,
        to_addr=to_addr,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        model=model,
        top_n=top_n,
    )
    typer.echo(f"Config written to: {config}")


def _setup_interactive(
    *,
    config: Path,
    from_addr: str | None,
    to_addr: str | None,
    smtp_host: str | None,
    smtp_port: int | None,
    model: str | None,
    top_n: int | None,
) -> None:
    """Prompt the user for all settings interactively, then write config and .env.

    Args:
        config: Destination path for the TOML config file.
        from_addr: Pre-filled sender address (used as default prompt value).
        to_addr: Pre-filled recipient address (used as default prompt value).
        smtp_host: Pre-filled SMTP host (used as default prompt value).
        smtp_port: Pre-filled SMTP port (used as default prompt value).
        model: Pre-filled AI model identifier (used as default prompt value).
        top_n: Pre-filled article count (used as default prompt value).
    """
    typer.echo("minizen setup wizard")
    typer.echo("--------------------")

    resolved_model = typer.prompt("AI model", default=model or DEFAULT_MODEL)
    resolved_top_n = typer.prompt(
        "Number of top articles", default=top_n or DEFAULT_TOP_N
    )
    resolved_smtp_host = typer.prompt(
        "SMTP host", default=smtp_host or DEFAULT_SMTP_HOST
    )
    resolved_smtp_port = typer.prompt(
        "SMTP port", default=smtp_port or DEFAULT_SMTP_PORT
    )
    resolved_from_addr = typer.prompt("From email address", default=from_addr or "")
    resolved_to_addr = typer.prompt("To email address", default=to_addr or "")
    email_username = typer.prompt("Email username (SMTP login)")
    email_password = typer.prompt("Email password (App Password)", hide_input=True)
    miniflux_api_key = typer.prompt("Miniflux API key", hide_input=True)

    key_label, key_env_var = _provider_key_info(resolved_model)
    ai_api_key = typer.prompt(key_label, hide_input=True)

    _write_config(
        config=config,
        from_addr=resolved_from_addr,
        to_addr=resolved_to_addr,
        smtp_host=resolved_smtp_host,
        smtp_port=int(resolved_smtp_port),
        model=resolved_model,
        top_n=int(resolved_top_n),
    )

    env_path = config.parent / ".env"
    env_path.write_text(
        f"MINIFLUX_API_KEY={miniflux_api_key}\n"
        f"{key_env_var}={ai_api_key}\n"
        f"MINIZEN_EMAIL_USERNAME={email_username}\n"
        f"MINIZEN_EMAIL_PASSWORD={email_password}\n"
    )
    env_path.chmod(0o600)

    typer.echo(f"\nConfig written to:      {config}")
    typer.echo(f"Credentials written to: {env_path}")


def _write_config(
    *,
    config: Path,
    from_addr: str,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    model: str,
    top_n: int,
) -> None:
    """Serialise the given settings to a TOML file, creating parent directories.

    Args:
        config: Destination path for the TOML config file.
        from_addr: Sender email address.
        to_addr: Recipient email address.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        model: AI model identifier.
        top_n: Number of top articles to include in the digest.
    """
    data = {
        "miniflux": {
            "url": DEFAULT_MINIFLUX_URL,
        },
        "email": {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "from_addr": from_addr,
            "to_addr": to_addr,
        },
        "ai": {
            "model": model,
            "top_n": top_n,
        },
    }
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(tomli_w.dumps(data).encode())
