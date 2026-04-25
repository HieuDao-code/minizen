import typer

from minizen.cli.commands import (
    config as config_module,
    digest as digest_module,
)
from minizen.cli.commands.run import run
from minizen.cli.commands.setup import setup

app = typer.Typer(
    name="minizen",
    help="A quieter way to stay informed.",
    no_args_is_help=True,
)


@app.callback()
def _callback() -> None:
    pass


app.command("run")(run)
app.command("setup")(setup)
app.add_typer(config_module.app, name="config")
app.add_typer(digest_module.app, name="digest")
