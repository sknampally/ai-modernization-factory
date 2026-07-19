"""Command-line interface for AIMF."""

from pathlib import Path
from typing import Annotated

import typer

from aimf import __version__
from aimf.config import load_settings
from aimf.logging_config import configure_logging
from aimf.services.analysis_service import AnalysisService
from aimf.services.analyzers import (
    CompositeAnalyzer,
    RepositoryMetricsAnalyzer,
)
from aimf.services.detectors.composite_technology_detector import (
    CompositeTechnologyDetector,
)
from aimf.services.detectors.java_technology_detector import (
    JavaTechnologyDetector,
)
from aimf.services.detectors.javascript_technology_detector import (
    JavaScriptTechnologyDetector,
)
from aimf.services.detectors.php_technology_detector import (
    PhpTechnologyDetector,
)
from aimf.services.scanners.github_repository_scanner import (
    GitHubRepositoryScanner,
)

configure_logging()

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
    """Clone and analyze the configured public GitHub repository."""

    settings = load_settings(config)

    scanner = GitHubRepositoryScanner(
        workspace_directory=settings.workspace.directory,
        branch=settings.repository.branch,
        clean_before_clone=settings.workspace.clean_before_clone,
    )

    repository = scanner.scan(str(settings.repository.url))

    technology_detector = CompositeTechnologyDetector(
        detectors=[
            JavaTechnologyDetector(),
            JavaScriptTechnologyDetector(),
            PhpTechnologyDetector(),
        ]
    )

    analysis_service = AnalysisService(
        technology_detector=technology_detector,
        analyzer=CompositeAnalyzer(
            analyzers=[
                RepositoryMetricsAnalyzer(),
            ]
        ),
        analyzer_version=__version__,
    )

    result = analysis_service.analyze(repository)

    typer.echo(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
