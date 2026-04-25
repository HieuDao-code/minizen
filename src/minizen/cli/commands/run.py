from pathlib import Path
from typing import Annotated

import typer

from minizen.config.loader import load_settings
from minizen.core.pipeline import run_pipeline

_DEFAULT_CONFIG = Path.home() / ".config" / "minizen" / "config.toml"


def run(
    config: Annotated[
        Path,
        typer.Option(help="Path to the TOML configuration file.", show_default=True),
    ] = _DEFAULT_CONFIG,
) -> None:
    """Run the full digest pipeline: fetch, summarise, and email."""
    try:
        settings = load_settings(config_path=config)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)
    run_pipeline(settings=settings)
