"""Main CLI entry point for ptracker."""

import typer
from ptracker.cli.init import init_command
from ptracker.cli import account, trade, query
from ptracker import __version__


def version_callback(value: bool):
    """Callback for --version option."""
    if value:
        typer.echo(f"ptracker version {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="ptracker",
    help="Personal investment portfolio tracking CLI tool",
    add_completion=False,
)

# Add sub-commands
app.add_typer(account.app, name="account")
app.add_typer(trade.app, name="trade")
app.add_typer(query.app, name="query")


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
):
    """Personal investment portfolio tracking CLI tool."""
    pass


@app.command()
def init():
    """Initialize ptracker data directory and configuration files."""
    init_command()


@app.command()
def version():
    """Display ptracker version."""
    from ptracker import __version__
    typer.echo(f"ptracker version {__version__}")


if __name__ == "__main__":
    app()