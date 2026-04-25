from pathlib import Path
from typing import Annotated

import typer

from minizen.config.loader import load_settings
from minizen.core.pipeline import run_pipeline

_DEFAULT_CONFIG = Path.home() / ".config" / "minizen" / "config.toml"

_DRY_RUN_OPTION = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Fetch articles but skip LLM call, email send, and mark-as-read.",
    ),
]


def run(
    config: Annotated[
        Path,
        typer.Option(help="Path to the TOML configuration file.", show_default=True),
    ] = _DEFAULT_CONFIG,
    dry_run: _DRY_RUN_OPTION = False,
) -> None:
    """Run the full digest pipeline: fetch, summarise, and email."""
    try:
        settings = load_settings(config_path=config)
    except FileNotFoundError:
        typer.echo(f"Config file not found: {config}")
        typer.echo("Run `minizen setup` to create one.")
        raise typer.Exit(code=1)
    except KeyError as e:
        typer.echo(f"Error: missing environment variable {e.args[0]}")
        raise typer.Exit(code=1)
    run_pipeline(settings=settings, dry_run=dry_run)
