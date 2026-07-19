"""Command-line interface for AIMF."""

from pathlib import Path
from typing import Annotated

import typer

from aimf import __version__
from aimf.config import load_settings
from aimf.services import GitHubRepositoryScanner

app = typer.Typer(
    name="aimf",
    help="Analyze and modernize legacy enterprise applications.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Display the AIMF application version."""

    typer.echo(f"AI Modernization Factory {__version__}")


@app.command()
def scan(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the AIMF TOML configuration file.",
        ),
    ] = Path("aimf.toml"),
) -> None:
    """Clone and scan the configured public GitHub repository."""

    settings = load_settings(config)

    scanner = GitHubRepositoryScanner(
        workspace_directory=settings.workspace.directory,
        branch=settings.repository.branch,
        clean_before_clone=(
            settings.workspace.clean_before_clone
        ),
    )

    repository = scanner.scan(
        str(settings.repository.url)
    )

    typer.echo(repository.model_dump_json(indent=2))


if __name__ == "__main__":
    app()