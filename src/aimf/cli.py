"""Command-line interface for AIMF."""

from pathlib import Path
from typing import Annotated

import typer

from aimf import __version__
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
from aimf.repository_auth.exceptions import RepositoryAccessError
from aimf.result_renderer import render_json
from aimf.services.analysis_service import AnalysisService
from aimf.services.analyzers import (
    ArchitectureAnalyzer,
    BuildDiscoveryAnalyzer,
    BuildMetadataAnalyzer,
    CicdDiscoveryAnalyzer,
    CloudReadinessAnalyzer,
    CompositeAnalyzer,
    DependencyDiscoveryAnalyzer,
    DependencyHealthAnalyzer,
    DependencyMetadataAnalyzer,
    RepositoryMetricsAnalyzer,
    SecurityAnalyzer,
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
from aimf.services.scan_comparison_service import ScanComparisonService
from aimf.services.scanners.github_repository_scanner import (
    GitHubRepositoryScanner,
)
from aimf.static_analysis.exceptions import StaticAnalysisProviderError
from aimf.static_analysis.providers import PmdProvider
from aimf.static_analysis.service import StaticAnalysisService

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
    """Clone and analyze the configured GitHub repository."""

    settings = load_settings(config)

    scanner = GitHubRepositoryScanner(
        workspace_directory=settings.workspace.directory,
        branch=settings.repository.branch,
        clean_before_clone=settings.workspace.clean_before_clone,
        authentication=settings.repository.authentication,
    )

    try:
        repository = scanner.scan(settings.repository.url)
    except RepositoryAccessError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    technology_detector = CompositeTechnologyDetector(
        detectors=[
            JavaTechnologyDetector(),
            JavaScriptTechnologyDetector(),
            PhpTechnologyDetector(),
        ]
    )

    static_analysis_settings = settings.static_analysis
    providers = []
    if static_analysis_settings.enabled and static_analysis_settings.pmd.enabled:
        providers.append(
            PmdProvider(
                executable=static_analysis_settings.pmd.executable,
                rulesets=static_analysis_settings.pmd.rulesets,
                minimum_priority=static_analysis_settings.pmd.minimum_priority,
                timeout_seconds=static_analysis_settings.pmd.timeout_seconds,
                enabled=True,
            )
        )

    static_analysis_service = StaticAnalysisService(
        providers=providers,
        enabled=static_analysis_settings.enabled,
        fail_on_provider_error=static_analysis_settings.fail_on_provider_error,
    )

    analysis_service = AnalysisService(
        technology_detector=technology_detector,
        analyzer=CompositeAnalyzer(
            analyzers=[
                RepositoryMetricsAnalyzer(),
                BuildDiscoveryAnalyzer(),
                BuildMetadataAnalyzer(),
                DependencyDiscoveryAnalyzer(),
                DependencyMetadataAnalyzer(),
                DependencyHealthAnalyzer(),
                CicdDiscoveryAnalyzer(),
                SecurityAnalyzer(),
                ArchitectureAnalyzer(),
                CloudReadinessAnalyzer(),
            ]
        ),
        analyzer_version=__version__,
        static_analysis_service=static_analysis_service,
    )

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


if __name__ == "__main__":
    app()
