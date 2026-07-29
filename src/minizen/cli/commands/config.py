"""CLI commands to inspect and update the minizen configuration."""

import contextlib
import os
import tomllib
from pathlib import Path
from typing import Annotated

import tomli_w
import typer

from minizen.ai.provider_keys import resolve_provider_key
from minizen.config.defaults import DEFAULT_CONFIG_PATH, DEFAULT_MODEL, DEFAULT_TOP_N
from minizen.config.loader import load_settings
from minizen.exceptions import ConfigError, UnsupportedProviderError

_CONFIG_OPTION = Annotated[
    Path,
    typer.Option(help="Path to the TOML configuration file.", show_default=True),
]

app = typer.Typer(help="Inspect and update configuration.")


def _check_model(model: str) -> None:
    """Exit with an error when *model* is not a usable model identifier.

    A provider the wizard cannot configure is accepted: the identifier is
    valid and works once the user sets up its environment.

    Args:
        model: pydantic-ai model identifier from the config file.

    Raises:
        typer.Exit: If the identifier is malformed, names an unknown provider,
            or needs an uninstalled package.
    """
    try:
        resolve_provider_key(model=model)
    except UnsupportedProviderError:
        return
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc


@app.command("show")
def show(config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH) -> None:
    """Display the current configuration."""
    try:
        with config.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)

    typer.echo(f"Config file: {config}")
    mf = data.get("miniflux", {})
    em = data.get("email", {})
    ai = data.get("ai", {})
    typer.echo(f"  miniflux.url:       {mf.get('url', '(unset)')}")
    typer.echo(f"  miniflux.api_key:   {'(from env)' if mf.get('url') else '(unset)'}")
    typer.echo(f"  email.smtp_host:    {em.get('smtp_host', '(unset)')}")
    typer.echo(f"  email.smtp_port:    {em.get('smtp_port', '(unset)')}")
    typer.echo(f"  email.from_addr:    {em.get('from_addr', '(unset)')}")
    typer.echo(f"  email.to_addr:      {em.get('to_addr', '(unset)')}")
    typer.echo(f"  ai.model:           {ai.get('model', DEFAULT_MODEL)}")
    typer.echo(f"  ai.top_n:           {ai.get('top_n', DEFAULT_TOP_N)}")


@app.command("validate")
def validate(config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH) -> None:
    """Validate the configuration file and environment variables."""
    try:
        settings = load_settings(config_path=config)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)

    try:
        provider = resolve_provider_key(model=settings.ai.model)
    except UnsupportedProviderError:
        typer.echo(f"AI provider configured manually: {settings.ai.model}")
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc
    else:
        if not os.environ.get(provider.env_var):
            typer.echo(f"Error: missing environment variable {provider.env_var}")
            raise typer.Exit(code=1)

    typer.echo("Configuration is valid.")


_ALLOWED_KEYS = {
    "miniflux.url",
    "ai.model",
    "ai.top_n",
    "email.smtp_host",
    "email.smtp_port",
    "email.from_addr",
    "email.to_addr",
}


@app.command("set")
def set_value(
    key: Annotated[
        str, typer.Argument(help="Dot-separated config key (e.g. ai.top_n).")
    ],
    value: Annotated[str, typer.Argument(help="New value.")],
    config: _CONFIG_OPTION = DEFAULT_CONFIG_PATH,
) -> None:
    """Set a configuration value in the TOML file."""
    if key not in _ALLOWED_KEYS:
        allowed = ", ".join(sorted(_ALLOWED_KEYS))
        typer.echo(f"Error: unknown config key '{key}'. Allowed: {allowed}")
        raise typer.Exit(code=1)

    if key == "ai.model":
        _check_model(value)

    try:
        with config.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)

    section, field = key.split(".", 1)
    if section not in data:
        data[section] = {}

    # Coerce numeric strings to int
    coerced: str | int = value
    with contextlib.suppress(ValueError):
        coerced = int(value)

    data[section][field] = coerced
    config.write_bytes(tomli_w.dumps(data).encode())
    typer.echo(f"Set {key} = {coerced!r}")
