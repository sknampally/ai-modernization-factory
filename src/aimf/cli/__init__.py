"""Command-line interface for AIMF."""

from pathlib import Path
from typing import Annotated

import typer

from aimf import __version__
from aimf.cli.assess import (
    DEFAULT_ASSESS_MAX_OUTPUT_TOKENS,
    DEFAULT_ASSESS_OUTPUT_DIRECTORY,
    DEFAULT_ASSESS_REPORT_TITLE,
    DEFAULT_ASSESS_TEMPERATURE,
    AssessmentApplicationService,
    AssessmentCommandError,
    AssessmentCommandResult,
    register_assess_command,
    run_assessment,
)
from aimf.config import load_settings
from aimf.logging_config import configure_logging
from aimf.output_format import OutputFormat
from aimf.reporters import (
    ConsoleReporter,
    HtmlFileReporter,
    JsonFileReporter,
    TextFileReporter,
    create_report_paths,
    retain_recent_reports,
)
from aimf.reporting import AssessmentMode
from aimf.repository_auth.exceptions import RepositoryAccessError
from aimf.result_renderer import render_json
from aimf.services.default_pipeline import create_default_analysis_service
from aimf.services.scan_comparison_service import ScanComparisonService
from aimf.services.scanners.github_repository_scanner import (
    GitHubRepositoryScanner,
)
from aimf.static_analysis.exceptions import StaticAnalysisProviderError

configure_logging()

app = typer.Typer(
    name="aimf",
    help=(
        "Analyze and modernize legacy enterprise applications.\n\n"
        "Canonical assessment workflow:\n"
        "  aimf assess --config aimf.toml --output reports --with-ai"
    ),
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
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format.",
            case_sensitive=False,
        ),
    ] = OutputFormat.TEXT,
    report_directory: Annotated[
        Path,
        typer.Option(
            "--report-directory",
            help="Directory where analysis reports are written.",
        ),
    ] = Path("reports"),
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Display the complete report in the terminal.",
        ),
    ] = False,
) -> None:
    """Clone and analyze the GitHub repository configured in aimf.toml."""

    try:
        settings = load_settings(config)
    except (FileNotFoundError, ValueError, OSError) as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if not settings.repository.url:
        typer.secho(
            "aimf scan requires [repository].url in the configuration file.\n\n"
            "Fix: set a GitHub URL in aimf.toml, for example:\n"
            "  [repository]\n"
            '  url = "https://github.com/YOUR_ORG/YOUR_REPO"\n'
            '  branch = "main"\n\n'
            "For a local checkout, use:\n"
            "  aimf assess --repo /path/to/repo --output reports",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    scanner = GitHubRepositoryScanner(
        workspace_directory=settings.workspace.directory,
        branch=settings.repository.branch,
        clean_before_clone=settings.workspace.clean_before_clone,
        authentication=settings.repository.authentication,
    )

    try:
        repository = scanner.scan(settings.repository.url)
    except RepositoryAccessError as error:
        typer.secho(
            f"{error}\n\n"
            "Fix: verify the repository URL, network access, and authentication "
            "(AIMF_GITHUB_TOKEN or SSH agent). See README troubleshooting.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from error

    analysis_service = create_default_analysis_service(settings)

    try:
        result = analysis_service.analyze(repository)
    except StaticAnalysisProviderError as exc:
        typer.secho(f"Static analysis failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    report_paths = create_report_paths(
        result=result,
        base_directory=report_directory,
    )

    comparison = ScanComparisonService().compare(
        current=result,
        repository_directory=report_paths.directory.parent,
        current_run_directory=report_paths.directory,
        current_timestamp=report_paths.timestamp,
    )
    result = result.model_copy(update={"comparison": comparison})

    TextFileReporter().write(
        result=result,
        output_path=report_paths.text_report,
    )

    JsonFileReporter().write(
        result=result,
        output_path=report_paths.json_report,
    )

    HtmlFileReporter().write(
        result=result,
        output_path=report_paths.html_report,
    )

    retain_recent_reports(report_paths.directory.parent)

    if output == OutputFormat.JSON:
        render_json(result)
        return

    console_reporter = ConsoleReporter()

    if verbose:
        console_reporter.render_detailed(result)
        return

    console_reporter.render_summary(
        result=result,
        text_report_path=report_paths.text_report,
        json_report_path=report_paths.json_report,
        html_report_path=report_paths.html_report,
    )


register_assess_command(app)

__all__ = [
    "DEFAULT_ASSESS_MAX_OUTPUT_TOKENS",
    "DEFAULT_ASSESS_OUTPUT_DIRECTORY",
    "DEFAULT_ASSESS_REPORT_TITLE",
    "DEFAULT_ASSESS_TEMPERATURE",
    "AssessmentApplicationService",
    "AssessmentCommandError",
    "AssessmentCommandResult",
    "AssessmentMode",
    "app",
    "run_assessment",
    "scan",
    "version",
]


if __name__ == "__main__":
    app()
