from pathlib import Path
from typing import Annotated

import tomli_w
import typer

_DEFAULT_CONFIG = Path.home() / ".config" / "minizen" / "config.toml"

_DEFAULT_MODEL = "anthropic:claude-sonnet-4-6"
_DEFAULT_TOP_N = 5


def setup(
    config: Annotated[
        Path,
        typer.Option(help="Path to write the TOML configuration file."),
    ] = _DEFAULT_CONFIG,
) -> None:
    """Interactive wizard to create a minizen configuration file."""
    typer.echo("minizen setup wizard")
    typer.echo("--------------------")

    miniflux_url = typer.prompt("Miniflux URL")
    smtp_host = typer.prompt("SMTP host")
    smtp_port = typer.prompt("SMTP port", default=587)
    from_addr = typer.prompt("From email address")
    to_addr = typer.prompt("To email address")
    model = typer.prompt("AI model", default=_DEFAULT_MODEL)
    top_n = typer.prompt("Number of top articles", default=_DEFAULT_TOP_N)

    data = {
        "miniflux": {"url": miniflux_url},
        "email": {
            "smtp_host": smtp_host,
            "smtp_port": int(smtp_port),
            "from_addr": from_addr,
            "to_addr": to_addr,
        },
        "ai": {
            "model": model,
            "top_n": int(top_n),
        },
    }

    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(tomli_w.dumps(data).encode())

    typer.echo(f"\nConfig written to: {config}")
    typer.echo("\nRemember to set the following environment variables:")
    typer.echo("  MINIFLUX_API_KEY  — your Miniflux API key")
    typer.echo("  EMAIL_USERNAME    — your SMTP username")
    typer.echo("  EMAIL_PASSWORD    — your SMTP password")
