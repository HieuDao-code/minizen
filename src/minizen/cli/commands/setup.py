from pathlib import Path
from typing import Annotated

import tomli_w
import typer

_DEFAULT_CONFIG = Path.home() / ".config" / "minizen" / "config.toml"
_DEFAULT_ENV = Path.home() / ".config" / "minizen" / ".env"

_DEFAULT_MODEL = "anthropic:claude-haiku-4-5"
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

    miniflux_api_key = typer.prompt("Miniflux API key", hide_input=True)
    anthropic_api_key = typer.prompt("Anthropic API key", hide_input=True)
    smtp_host = typer.prompt("SMTP host", default="smtp.gmail.com")
    smtp_port = typer.prompt("SMTP port", default=587)
    from_addr = typer.prompt("From email address")
    to_addr = typer.prompt("To email address")
    email_username = typer.prompt("Email username (SMTP login)")
    email_password = typer.prompt("Email password (App Password)", hide_input=True)
    model = typer.prompt("AI model", default=_DEFAULT_MODEL)
    top_n = typer.prompt("Number of top articles", default=_DEFAULT_TOP_N)

    config_data = {
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
    config.write_bytes(tomli_w.dumps(config_data).encode())

    env_path = config.parent / ".env"
    env_path.write_text(
        f"MINIFLUX_API_KEY={miniflux_api_key}\n"
        f"ANTHROPIC_API_KEY={anthropic_api_key}\n"
        f"MINIZEN_EMAIL_USERNAME={email_username}\n"
        f"MINIZEN_EMAIL_PASSWORD={email_password}\n"
    )

    typer.echo(f"\nConfig written to:      {config}")
    typer.echo(f"Credentials written to: {env_path}")
