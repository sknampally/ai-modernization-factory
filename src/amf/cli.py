"""Command-line interface for AI Modernization Factory."""

import typer

app = typer.Typer(
    name="ai-factory",
    help="Analyze and modernize legacy enterprise applications.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """AI Modernization Factory command-line interface."""


@app.command()
def version() -> None:
    """Display the installed application version."""
    typer.echo("AI Modernization Factory 0.1.0")


if __name__ == "__main__":
    app()