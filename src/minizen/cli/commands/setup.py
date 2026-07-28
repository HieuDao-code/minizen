"""Interactive and non-interactive setup wizard for minizen."""

import os
from pathlib import Path
from typing import Annotated

import tomli_w
import typer

from minizen.ai.provider_keys import ProviderKey, resolve_provider_key
from minizen.config.defaults import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MINIFLUX_URL,
    DEFAULT_MODEL,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_TOP_N,
)
from minizen.exceptions import ConfigError


def _provider_key(model: str) -> ProviderKey:
    """Resolve the provider API key for *model*, exiting on any failure.

    Args:
        model: pydantic-ai model identifier (e.g. ``deepseek:deepseek-chat``).

    Returns:
        The ``ProviderKey`` describing the required API key.

    Raises:
        typer.Exit: If the identifier is invalid, names an unknown provider,
            needs an uninstalled package, or cannot be configured by the wizard.
    """
    try:
        return resolve_provider_key(model=model)
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc


def _parse_comma_list(value: str | None) -> list[str]:
    """Split a comma-separated string into a stripped list, dropping empty items.

    Args:
        value: Raw comma-separated string, or ``None``.

    Returns:
        List of stripped non-empty strings. Returns ``[]`` for ``None`` or blank input.
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


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
    interests: Annotated[
        str | None,
        typer.Option("--interests", help="Comma-separated topics to prioritise."),
    ] = None,
    avoid: Annotated[
        str | None,
        typer.Option("--avoid", help="Comma-separated topics to avoid."),
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
            interests=_parse_comma_list(interests),
            avoid=_parse_comma_list(avoid),
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
            interests=interests,
            avoid=avoid,
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
    interests: list[str],
    avoid: list[str],
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
        interests: Topics to prioritise when selecting articles.
        avoid: Topics to exclude when selecting articles.
    """
    if not from_addr:
        typer.echo("Error: --from-addr is required in non-interactive mode.")
        raise typer.Exit(code=1)
    if not to_addr:
        typer.echo("Error: --to-addr is required in non-interactive mode.")
        raise typer.Exit(code=1)

    ai_key_var = _provider_key(model).env_var

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
        interests=interests,
        avoid=avoid,
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
    interests: str | None,
    avoid: str | None,
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
        interests: Pre-filled interests string (used as default prompt value).
        avoid: Pre-filled avoid string (used as default prompt value).
    """
    typer.echo("minizen setup wizard")
    typer.echo("--------------------")

    resolved_model = typer.prompt(
        "AI model (provider:model)", default=model or DEFAULT_MODEL
    )
    provider = _provider_key(resolved_model)
    resolved_top_n = typer.prompt(
        "Number of top articles", default=top_n or DEFAULT_TOP_N
    )
    interests_str = typer.prompt(
        "Topics to prioritise (comma-separated, Enter to skip)",
        default=interests or "",
    )
    avoid_str = typer.prompt(
        "Topics to avoid (comma-separated, Enter to skip)",
        default=avoid or "",
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

    ai_api_key = typer.prompt(provider.label, hide_input=True)

    _write_config(
        config=config,
        from_addr=resolved_from_addr,
        to_addr=resolved_to_addr,
        smtp_host=resolved_smtp_host,
        smtp_port=int(resolved_smtp_port),
        model=resolved_model,
        top_n=int(resolved_top_n),
        interests=_parse_comma_list(interests_str),
        avoid=_parse_comma_list(avoid_str),
    )

    env_path = config.parent / ".env"
    _write_secret_file(
        env_path,
        f"MINIFLUX_API_KEY={_quote_env_value(miniflux_api_key)}\n"
        f"{provider.env_var}={_quote_env_value(ai_api_key)}\n"
        f"MINIZEN_EMAIL_USERNAME={_quote_env_value(email_username)}\n"
        f"MINIZEN_EMAIL_PASSWORD={_quote_env_value(email_password)}\n",
    )

    typer.echo(f"\nConfig written to:      {config}")
    typer.echo(f"Credentials written to: {env_path}")


def _write_secret_file(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` in a file that only the owner can read.

    Creates the file atomically with ``0o600`` permissions so its contents are
    never briefly world- or group-readable between creation and a later
    ``chmod`` (the race the plain ``write_text`` + ``chmod`` sequence has). An
    existing file is truncated and re-secured to ``0o600``.

    Args:
        path: Destination path for the secret file.
        content: Text to write.
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    # Re-secure a pre-existing file, whose permissions O_CREAT leaves untouched.
    os.chmod(path, 0o600)


def _quote_env_value(value: str) -> str:
    r"""Wrap a .env value in double quotes, escaping backslashes and double quotes.

    Args:
        value: The raw credential string to quote.

    Returns:
        The value wrapped in double quotes with ``\\`` and ``"`` escaped,
        safe for writing to a ``.env`` file parsed by python-dotenv.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_config(
    *,
    config: Path,
    from_addr: str,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    model: str,
    top_n: int,
    interests: list[str],
    avoid: list[str],
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
        interests: Topics to prioritise; omitted from config when empty.
        avoid: Topics to exclude; omitted from config when empty.
    """
    ai_section: dict[str, object] = {"model": model, "top_n": top_n}
    if interests:
        ai_section["interests"] = interests
    if avoid:
        ai_section["avoid"] = avoid
    data: dict[str, object] = {
        "miniflux": {
            "url": DEFAULT_MINIFLUX_URL,
        },
        "email": {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "from_addr": from_addr,
            "to_addr": to_addr,
        },
        "ai": ai_section,
    }
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(tomli_w.dumps(data).encode())
