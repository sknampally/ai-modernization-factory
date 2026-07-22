"""End-to-end modernization assessment CLI orchestration."""

from __future__ import annotations

import os
import re
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Annotated, Protocol

import typer
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rich.console import Console

from aimf.ai.providers.parsing import sanitize_provider_text
from aimf.config import AimfSettings, load_settings
from aimf.logging_config import configure_logging
from aimf.models import AnalysisResult, Repository
from aimf.reporters.report_paths import (
    ReportArchiveError,
    ReportPaths,
    archive_excess_report_runs,
    create_report_paths,
    format_report_run_timestamp,
)
from aimf.reporting import (
    AssessmentMode,
    AssessmentTiming,
    ModernizationReportInput,
    ModernizationReportValidationError,
    write_modernization_assessment_reports,
)
from aimf.repository_auth.exceptions import (
    RepositoryAccessError,
    UnsupportedRepositoryUrlError,
)
from aimf.repository_auth.github_urls import parse_github_repository_url
from aimf.services.analysis_service import AnalysisService
from aimf.services.default_pipeline import create_default_analysis_service
from aimf.services.scanners.github_repository_scanner import GitHubRepositoryScanner
from aimf.services.scanners.local_repository_scanner import LocalRepositoryScanner
from aimf.static_analysis.exceptions import StaticAnalysisProviderError
from aimf.static_analysis.models import StaticAnalysisStatus
from aimf.static_analysis.providers.pmd_discovery import (
    AIMF_PMD_PATH_ENV,
    discovery_diagnostic_lines,
    probe_pmd_version,
    resolve_pmd_executable,
)

if TYPE_CHECKING:
    from aimf.ai.agents import ModernizationAssessmentAgent
    from aimf.ai.agents.models import ModernizationAssessmentResult
    from aimf.ai.contracts import LLMAnalysisContextBuilder
    from aimf.ai.contracts.models import LLMAnalysisContext
    from aimf.ai.prompts import ModernizationPromptBuilder
    from aimf.ai.providers.base import AIModelProvider

DEFAULT_ASSESS_OUTPUT_DIRECTORY = Path("reports")
DEFAULT_ASSESS_REPORT_TITLE = "Modernization Assessment"
DEFAULT_ASSESS_TEMPERATURE = 0.0
DEFAULT_ASSESS_MAX_OUTPUT_TOKENS = 5000
AIMF_BEDROCK_MODEL_ID_ENV = "AIMF_BEDROCK_MODEL_ID"


class AssessmentCommandError(Exception):
    """CLI-facing assessment failure."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class AssessmentCommandResult(BaseModel):
    """Immutable summary returned by a successful assess run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_name: str = Field(min_length=1)
    run_directory: Path
    html_report_path: Path
    json_report_path: Path
    report_path: Path | None = None
    mode: AssessmentMode
    findings_count: int = Field(ge=0)
    technologies_count: int = Field(ge=0)
    recommendations_count: int = Field(ge=0)
    phases_count: int = Field(ge=0)
    ai_executed: bool
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    model_id: str | None = None
    latency_ms: float | None = Field(default=None, ge=0.0)
    duration_ms: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def populate_report_path_alias(self) -> AssessmentCommandResult:
        if self.report_path is None:
            return self.model_copy(update={"report_path": self.html_report_path})
        return self


class _RepositoryScanner(Protocol):
    def scan(self, source: str | Path) -> Repository:
        """Scan a repository source and return repository metadata."""


def run_assessment(
    repo: str,
    output_directory: Path,
    *,
    mode: AssessmentMode = AssessmentMode.DETERMINISTIC,
    model_id: str | None = None,
    branch: str | None = None,
    report_title: str = DEFAULT_ASSESS_REPORT_TITLE,
    organization_name: str | None = None,
    max_output_tokens: int = DEFAULT_ASSESS_MAX_OUTPUT_TOKENS,
    temperature: float = DEFAULT_ASSESS_TEMPERATURE,
    max_context_characters: int | None = None,
    include_raw_model_response: bool = False,
    pmd_path: str | None = None,
    pmd_profile: str | None = None,
    static_analysis_enabled: bool | None = None,
    config_path: Path = Path("aimf.toml"),
    settings: AimfSettings | None = None,
    analysis_service: AnalysisService | None = None,
    provider: AIModelProvider | None = None,
    prompt_builder: ModernizationPromptBuilder | None = None,
    agent: ModernizationAssessmentAgent | None = None,
    scanner: _RepositoryScanner | None = None,
    context_builder: LLMAnalysisContextBuilder | None = None,
    console: Console | None = None,
    clock: Callable[[], datetime] | None = None,
    verbose: bool = False,
) -> AssessmentCommandResult:
    """Orchestrate scan → analysis → optional AI assessment → HTML+JSON reports."""

    active_console = console or Console(stderr=False)
    now = clock or (lambda: datetime.now(UTC))
    total_started = perf_counter()

    def stage(message: str) -> None:
        active_console.print(f"[bold]{message}[/bold]")

    def warn(message: str) -> None:
        active_console.print(f"[yellow]Warning:[/yellow] {message}")

    try:
        loaded_settings = settings or load_settings(config_path)
    except (FileNotFoundError, ValueError, OSError) as error:
        raise AssessmentCommandError(sanitize_provider_text(str(error))) from error

    if pmd_profile is not None:
        from aimf.static_analysis.providers.pmd_profiles import parse_pmd_profile

        try:
            parse_pmd_profile(pmd_profile)
        except ValueError as error:
            raise AssessmentCommandError(sanitize_provider_text(str(error))) from error

    resolved_branch = branch if branch is not None else loaded_settings.repository.branch
    repository_reference = _safe_repository_reference(repo)

    stage("Scanning repository")
    scan_started = perf_counter()
    try:
        repository = _scan_repository(
            repo,
            settings=loaded_settings,
            branch=resolved_branch,
            scanner=scanner,
        )
    except AssessmentCommandError:
        raise
    except (
        FileNotFoundError,
        NotADirectoryError,
        UnsupportedRepositoryUrlError,
        RepositoryAccessError,
        OSError,
        ValueError,
    ) as error:
        raise AssessmentCommandError(
            f"Invalid repository path or URL: {sanitize_provider_text(str(error))}"
        ) from error
    scan_ms = round((perf_counter() - scan_started) * 1000, 2)

    stage("Detecting technologies")
    stage("Running deterministic analysis")
    analysis_started = perf_counter()
    resolved_pmd = _resolve_pmd_for_assessment(
        cli_path=pmd_path,
        settings=loaded_settings,
        verbose=verbose,
        console=active_console,
    )
    service = analysis_service or create_default_analysis_service(
        loaded_settings,
        pmd_executable=resolved_pmd,
        static_analysis_enabled=static_analysis_enabled,
        pmd_profile=pmd_profile,
    )
    try:
        analysis_result = service.analyze(repository)
    except StaticAnalysisProviderError as error:
        raise AssessmentCommandError(sanitize_provider_text(str(error))) from error
    except Exception as error:  # noqa: BLE001 - CLI boundary
        raise AssessmentCommandError(
            f"Deterministic analysis failed: {sanitize_provider_text(str(error))}"
        ) from error
    analysis_ms = round((perf_counter() - analysis_started) * 1000, 2)

    static_analysis_ms = _static_analysis_duration_ms(analysis_result)
    warnings = _static_analysis_warnings(analysis_result)
    for message in warnings:
        warn(message)
    _print_static_analysis_success(active_console, analysis_result)

    analysis_context: LLMAnalysisContext | None = None
    assessment_result: ModernizationAssessmentResult | None = None
    ai_ms: float | None = None

    if mode == AssessmentMode.AI_ENHANCED:
        from aimf.ai.prompts.models import DEFAULT_MAX_CONTEXT_CHARACTERS

        resolved_model_id = resolve_bedrock_model_id(
            cli_model_id=model_id,
            settings=loaded_settings,
        )
        context_limit = (
            max_context_characters
            if max_context_characters is not None
            else DEFAULT_MAX_CONTEXT_CHARACTERS
        )
        ai_started = perf_counter()
        analysis_context, assessment_result = _run_ai_assessment(
            analysis_result=analysis_result,
            settings=loaded_settings,
            resolved_model_id=resolved_model_id,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            context_limit=context_limit,
            include_raw_model_response=include_raw_model_response,
            provider=provider,
            prompt_builder=prompt_builder,
            agent=agent,
            context_builder=context_builder,
            stage=stage,
        )
        ai_ms = round((perf_counter() - ai_started) * 1000, 2)

    stage("Generating HTML and JSON reports")
    generated_at = now()
    run_timestamp = format_report_run_timestamp(generated_at)
    report_paths = create_report_paths(
        analysis_result,
        output_directory,
        timestamp=run_timestamp,
        create_directory=False,
    )
    provisional_total = round((perf_counter() - total_started) * 1000, 2)
    report_input = ModernizationReportInput(
        analysis_result=analysis_result,
        assessment_mode=mode,
        analysis_context=analysis_context,
        assessment_result=assessment_result,
        generated_at_utc=generated_at,
        report_title=report_title.strip() or DEFAULT_ASSESS_REPORT_TITLE,
        organization_name=organization_name,
        repository_reference=repository_reference,
        warnings=tuple(warnings),
        timing=AssessmentTiming(
            total_ms=provisional_total,
            scan_ms=scan_ms,
            analysis_ms=analysis_ms,
            static_analysis_ms=static_analysis_ms,
            ai_ms=ai_ms,
            report_ms=None,
        ),
    )

    try:
        written_paths = write_modernization_assessment_reports(
            report_input,
            report_paths,
        )
    except ModernizationReportValidationError as error:
        raise AssessmentCommandError(
            f"Report validation or write failure: {sanitize_provider_text(str(error))}"
        ) from error
    except OSError as error:
        raise AssessmentCommandError(
            f"Report validation or write failure: {sanitize_provider_text(str(error))}"
        ) from error
    except Exception as error:  # noqa: BLE001 - CLI boundary
        raise AssessmentCommandError(
            f"Report validation or write failure: {sanitize_provider_text(str(error))}"
        ) from error

    try:
        archive_excess_report_runs(written_paths.run_directory.parent)
    except ReportArchiveError as error:
        raise AssessmentCommandError(
            f"Report retention failure: {sanitize_provider_text(str(error))}"
        ) from error
    except OSError as error:
        raise AssessmentCommandError(
            f"Report retention failure: {sanitize_provider_text(str(error))}"
        ) from error

    total_ms = round((perf_counter() - total_started) * 1000, 2)

    result = _build_command_result(
        repository_name=repository.name,
        report_paths=written_paths,
        mode=mode,
        analysis_result=analysis_result,
        assessment_result=assessment_result,
        duration_ms=total_ms,
    )
    _print_success_summary(active_console, result)
    return result


def resolve_bedrock_model_id(
    *,
    cli_model_id: str | None,
    settings: AimfSettings,
) -> str:
    """Resolve Bedrock model ID from CLI, environment, then config."""

    if cli_model_id and cli_model_id.strip():
        return cli_model_id.strip()

    env_model_id = os.environ.get(AIMF_BEDROCK_MODEL_ID_ENV)
    if env_model_id and env_model_id.strip():
        return env_model_id.strip()

    configured = settings.ai.bedrock.model_id
    if configured and configured.strip():
        return configured.strip()

    raise AssessmentCommandError(
        "Missing Bedrock model ID. Provide --model-id, set "
        f"{AIMF_BEDROCK_MODEL_ID_ENV}, or configure ai.bedrock.model_id."
    )


def modernization_report_basename(repository_name: str) -> str:
    """Return a sanitized assessment report basename (without extension)."""

    return f"{_slugify(repository_name)}-modernization-assessment"


def modernization_report_filename(repository_name: str) -> str:
    """Return a sanitized HTML report filename for a repository."""

    return f"{modernization_report_basename(repository_name)}.html"


def modernization_json_report_filename(repository_name: str) -> str:
    """Return a sanitized JSON report filename for a repository."""

    return f"{modernization_report_basename(repository_name)}.json"


def is_github_repository_source(repo: str) -> bool:
    """Return whether the repo argument is a GitHub URL."""

    try:
        parse_github_repository_url(repo)
    except UnsupportedRepositoryUrlError:
        return False
    return True


def _resolve_pmd_for_assessment(
    *,
    cli_path: str | None,
    settings: AimfSettings,
    verbose: bool,
    console: Console,
) -> str | None:
    if not settings.static_analysis.enabled or not settings.static_analysis.pmd.enabled:
        return None

    discovery = resolve_pmd_executable(
        cli_path=cli_path,
        configured=settings.static_analysis.pmd.executable,
    )
    if verbose:
        for line in discovery_diagnostic_lines(discovery):
            console.print(f"[dim]{line}[/dim]")
    if discovery.executable is None:
        return cli_path or settings.static_analysis.pmd.executable

    version = probe_pmd_version(discovery.executable)
    if verbose and version is not None:
        console.print(f"[dim]PMD version probe: {version}[/dim]")
    return discovery.executable


def _run_ai_assessment(
    *,
    analysis_result: AnalysisResult,
    settings: AimfSettings,
    resolved_model_id: str,
    temperature: float,
    max_output_tokens: int,
    context_limit: int,
    include_raw_model_response: bool,
    provider: AIModelProvider | None,
    prompt_builder: ModernizationPromptBuilder | None,
    agent: ModernizationAssessmentAgent | None,
    context_builder: LLMAnalysisContextBuilder | None,
    stage: Callable[[str], None],
) -> tuple[LLMAnalysisContext, ModernizationAssessmentResult]:
    from aimf.ai.agents import (
        AgentConfigurationError,
        AgentError,
        AgentExecutionError,
        AgentExecutionOptions,
        AgentValidationError,
        ModernizationAssessmentAgent,
    )
    from aimf.ai.contracts import LLMAnalysisContextBuilder
    from aimf.ai.prompts import ModernizationPromptBuilder, PromptBuildOptions
    from aimf.ai.providers.exceptions import (
        AIProviderError,
        AIProviderTimeoutError,
        AIResponseParsingError,
        AIResponseValidationError,
    )
    from aimf.ai.providers.models import ModelInvocationOptions

    stage("Building AI context")
    builder = context_builder or LLMAnalysisContextBuilder()
    try:
        analysis_context = builder.build(analysis_result)
    except Exception as error:  # noqa: BLE001 - CLI boundary
        raise AssessmentCommandError(
            f"Failed to build AI context: {sanitize_provider_text(str(error))}"
        ) from error

    stage("Running modernization assessment")
    active_prompt_builder = prompt_builder or ModernizationPromptBuilder()
    active_provider = provider or _create_bedrock_provider(settings)
    active_agent = agent or ModernizationAssessmentAgent(
        active_provider,
        prompt_builder=active_prompt_builder,
    )
    options = AgentExecutionOptions(
        model_options=ModelInvocationOptions(
            model_id=resolved_model_id,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
        prompt_options=PromptBuildOptions(
            max_context_characters=context_limit,
        ),
        include_raw_model_response=include_raw_model_response,
    )

    try:
        assessment_result = active_agent.run(analysis_context, options)
    except AgentValidationError as error:
        cause = error.__cause__
        if isinstance(cause, (AIResponseValidationError, AIResponseParsingError)):
            raise AssessmentCommandError(
                f"Invalid model response: {sanitize_provider_text(str(cause))}"
            ) from error
        raise AssessmentCommandError(
            f"Recommendation validation failure: {sanitize_provider_text(str(error))}"
        ) from error
    except AIProviderTimeoutError as error:
        raise AssessmentCommandError(
            f"Bedrock timeout or throttling: {sanitize_provider_text(str(error))}"
        ) from error
    except (AIResponseValidationError, AIResponseParsingError) as error:
        raise AssessmentCommandError(
            f"Invalid model response: {sanitize_provider_text(str(error))}"
        ) from error
    except AIProviderError as error:
        raise _map_provider_error(error) from error
    except (AgentConfigurationError, AgentExecutionError, AgentError) as error:
        cause = error.__cause__
        if isinstance(cause, AIProviderTimeoutError):
            raise AssessmentCommandError(
                f"Bedrock timeout or throttling: {sanitize_provider_text(str(cause))}"
            ) from error
        if isinstance(cause, (AIResponseValidationError, AIResponseParsingError)):
            raise AssessmentCommandError(
                f"Invalid model response: {sanitize_provider_text(str(cause))}"
            ) from error
        if isinstance(cause, AIProviderError):
            raise _map_provider_error(cause) from error
        raise AssessmentCommandError(sanitize_provider_text(str(error))) from error
    except Exception as error:  # noqa: BLE001 - CLI boundary
        raise AssessmentCommandError(
            f"Modernization assessment failed: {sanitize_provider_text(str(error))}"
        ) from error

    return analysis_context, assessment_result


def _map_provider_error(error: Exception) -> AssessmentCommandError:
    message = sanitize_provider_text(str(error))
    lowered = message.lower()
    if "authentication" in lowered or "access denied" in lowered:
        return AssessmentCommandError(f"AWS authentication or access denied: {message}")
    if "throttl" in lowered or "timed out" in lowered or "timeout" in lowered:
        return AssessmentCommandError(f"Bedrock timeout or throttling: {message}")
    return AssessmentCommandError(f"Model provider failure: {message}")


def _static_analysis_warnings(analysis_result: AnalysisResult) -> list[str]:
    warnings: list[str] = []
    for result in analysis_result.static_analysis_results:
        if result.status == StaticAnalysisStatus.UNAVAILABLE:
            warnings.append(
                f"{result.provider_name} static analysis was unavailable. "
                "Remaining deterministic analyzers completed."
            )
        elif result.status == StaticAnalysisStatus.FAILED:
            detail = result.error_message or "provider failed"
            warnings.append(
                f"{result.provider_name} static analysis failed: "
                f"{sanitize_provider_text(detail)}. "
                "Remaining deterministic analyzers completed."
            )
    return warnings


def _print_static_analysis_success(
    console: Console,
    analysis_result: AnalysisResult,
) -> None:
    for result in analysis_result.static_analysis_results:
        if result.status != StaticAnalysisStatus.COMPLETED:
            continue
        version = result.provider_version or "unknown"
        profile = result.profile or "standard"
        raw = result.raw_observation_count
        grouped = result.grouped_finding_count
        console.print(
            f"Static analysis: {result.provider_name} {version} "
            f"(profile={profile}, raw={raw}, grouped={grouped})"
        )


def _static_analysis_duration_ms(analysis_result: AnalysisResult) -> float | None:
    durations = [
        item.duration_ms
        for item in analysis_result.static_analysis_results
        if item.duration_ms is not None
    ]
    if not durations:
        return None
    return round(sum(durations), 2)


def _build_command_result(
    *,
    repository_name: str,
    report_paths: ReportPaths,
    mode: AssessmentMode,
    analysis_result: AnalysisResult,
    assessment_result: ModernizationAssessmentResult | None,
    duration_ms: float | None,
) -> AssessmentCommandResult:
    deterministic_recommendation_count = len(analysis_result.recommendations)
    if mode == AssessmentMode.AI_ENHANCED and assessment_result is not None:
        recommendation = assessment_result.recommendation_result
        metadata = assessment_result.model_metadata
        return AssessmentCommandResult(
            repository_name=repository_name,
            run_directory=report_paths.run_directory,
            html_report_path=report_paths.html_report_path,
            json_report_path=report_paths.json_report_path,
            report_path=report_paths.html_report_path,
            mode=mode,
            findings_count=len(analysis_result.findings),
            technologies_count=len(analysis_result.technologies),
            recommendations_count=deterministic_recommendation_count,
            phases_count=len(recommendation.modernization_phases),
            ai_executed=True,
            input_tokens=metadata.usage.input_tokens,
            output_tokens=metadata.usage.output_tokens,
            model_id=metadata.model_id,
            latency_ms=metadata.latency_ms,
            duration_ms=duration_ms,
        )

    return AssessmentCommandResult(
        repository_name=repository_name,
        run_directory=report_paths.run_directory,
        html_report_path=report_paths.html_report_path,
        json_report_path=report_paths.json_report_path,
        report_path=report_paths.html_report_path,
        mode=AssessmentMode.DETERMINISTIC,
        findings_count=len(analysis_result.findings),
        technologies_count=len(analysis_result.technologies),
        recommendations_count=deterministic_recommendation_count,
        phases_count=0,
        ai_executed=False,
        input_tokens=None,
        output_tokens=None,
        model_id=None,
        latency_ms=None,
        duration_ms=duration_ms,
    )


def _scan_repository(
    repo: str,
    *,
    settings: AimfSettings,
    branch: str | None,
    scanner: _RepositoryScanner | None,
) -> Repository:
    compact = repo.strip()
    if not compact:
        raise AssessmentCommandError("Invalid repository path or URL: repository is empty")

    if scanner is not None:
        return scanner.scan(compact)

    if is_github_repository_source(compact):
        github_scanner = GitHubRepositoryScanner(
            workspace_directory=settings.workspace.directory,
            branch=branch,
            clean_before_clone=settings.workspace.clean_before_clone,
            authentication=settings.repository.authentication,
        )
        return github_scanner.scan(compact)

    path = Path(compact)
    return LocalRepositoryScanner().scan(path)


def _create_bedrock_provider(settings: AimfSettings) -> AIModelProvider:
    from aimf.ai.providers.bedrock import BedrockAIModelProvider

    region = (
        settings.ai.bedrock.region
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
    )
    return BedrockAIModelProvider(region_name=region)


def _safe_repository_reference(repo: str) -> str:
    compact = repo.strip()
    if not compact:
        return "repository"
    if is_github_repository_source(compact):
        return compact
    path = Path(compact)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except (OSError, ValueError):
        if path.is_absolute():
            return path.name
        return str(path)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except (OSError, ValueError):
        return str(path)


def _print_success_summary(console: Console, result: AssessmentCommandResult) -> None:
    mode_label = "AI Enhanced" if result.mode == AssessmentMode.AI_ENHANCED else "Deterministic"
    console.print()
    console.print("[green]Modernization assessment completed[/green]")
    console.print(f"Assessment mode: {mode_label}")
    console.print(f"Repository: {result.repository_name}")
    console.print(f"Findings: {result.findings_count}")
    console.print(f"Technologies: {result.technologies_count}")
    console.print(f"Deterministic recommendations: {result.recommendations_count}")
    if result.ai_executed:
        console.print(f"Modernization phases: {result.phases_count}")
        console.print(
            f"Input tokens: {result.input_tokens if result.input_tokens is not None else '—'}"
        )
        console.print(
            f"Output tokens: {result.output_tokens if result.output_tokens is not None else '—'}"
        )
        console.print(f"Model ID: {result.model_id or '—'}")
        latency = f"{result.latency_ms:.2f}" if result.latency_ms is not None else "—"
        console.print(f"Assessment latency (ms): {latency}")
    console.print(f"Run directory: {_display_path(result.run_directory)}")
    console.print(f"HTML report: {_display_path(result.html_report_path)}")
    console.print(f"JSON report: {_display_path(result.json_report_path)}")
    if result.duration_ms is not None:
        console.print(f"Duration: {result.duration_ms / 1000:.1f}s")


def _slugify(value: str) -> str:
    compact = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", compact).strip("-")
    return slug or "repository"


def register_assess_command(app: typer.Typer) -> None:
    """Register the assess command on the AIMF Typer application."""

    @app.command("assess")
    def assess(
        repo: Annotated[
            str,
            typer.Option(
                "--repo",
                "-r",
                help="Local repository path or GitHub repository URL.",
            ),
        ],
        output: Annotated[
            Path,
            typer.Option(
                "--output",
                "-o",
                help="Directory where timestamped assessment reports are written.",
            ),
        ] = DEFAULT_ASSESS_OUTPUT_DIRECTORY,
        with_ai: Annotated[
            bool,
            typer.Option(
                "--with-ai/--no-ai",
                help=(
                    "Enable AI-enhanced assessment. Default is --no-ai "
                    "(deterministic evidence only; no cloud provider required)."
                ),
            ),
        ] = False,
        model_id: Annotated[
            str | None,
            typer.Option(
                "--model-id",
                help=(
                    "Bedrock model ID (required with --with-ai). Defaults to "
                    "AIMF_BEDROCK_MODEL_ID or ai.bedrock.model_id from configuration."
                ),
            ),
        ] = None,
        pmd_path: Annotated[
            str | None,
            typer.Option(
                "--pmd-path",
                help=(
                    "Optional path or command name for the PMD executable. "
                    f"Overrides {AIMF_PMD_PATH_ENV} and configuration."
                ),
            ),
        ] = None,
        pmd_profile: Annotated[
            str | None,
            typer.Option(
                "--pmd-profile",
                help=(
                    "PMD analysis profile: focused, standard, or comprehensive. "
                    "Overrides static_analysis.pmd.profile from configuration."
                ),
            ),
        ] = None,
        static_analysis: Annotated[
            bool,
            typer.Option(
                "--static-analysis/--no-static-analysis",
                help="Enable or disable external static analysis for this run.",
            ),
        ] = True,
        branch: Annotated[
            str | None,
            typer.Option(
                "--branch",
                help="Git branch for GitHub repositories.",
            ),
        ] = None,
        report_title: Annotated[
            str,
            typer.Option(
                "--report-title",
                help="Title shown in the HTML assessment report.",
            ),
        ] = DEFAULT_ASSESS_REPORT_TITLE,
        organization_name: Annotated[
            str | None,
            typer.Option(
                "--organization-name",
                help="Optional organization name for the HTML report header.",
            ),
        ] = None,
        max_output_tokens: Annotated[
            int,
            typer.Option(
                "--max-output-tokens",
                help="Maximum model output tokens (AI-enhanced mode only).",
            ),
        ] = DEFAULT_ASSESS_MAX_OUTPUT_TOKENS,
        temperature: Annotated[
            float,
            typer.Option(
                "--temperature",
                help="Model temperature (AI-enhanced mode only; default 0.0).",
            ),
        ] = DEFAULT_ASSESS_TEMPERATURE,
        max_context_characters: Annotated[
            int | None,
            typer.Option(
                "--max-context-characters",
                help="Maximum LLM analysis context JSON size in characters.",
            ),
        ] = None,
        include_raw_model_response: Annotated[
            bool,
            typer.Option(
                "--include-raw-model-response",
                help="Include raw model response in the assessment result payload.",
            ),
        ] = False,
        config: Annotated[
            Path,
            typer.Option(
                "--config",
                "-c",
                help="Path to the AIMF TOML configuration file.",
            ),
        ] = Path("aimf.toml"),
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable diagnostic logging and display stack traces for failures.",
            ),
        ] = False,
    ) -> None:
        """Run modernization assessment and write HTML and JSON reports."""

        configure_logging(level="DEBUG" if verbose else "WARNING")

        if model_id and model_id.strip() and not with_ai:
            typer.secho(
                "--model-id requires --with-ai. Deterministic assessment is the "
                "default and does not use a model.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=2)

        mode = AssessmentMode.AI_ENHANCED if with_ai else AssessmentMode.DETERMINISTIC
        # Typer defaults --static-analysis to True; treat as "follow config" unless
        # the user explicitly disabled with --no-static-analysis.
        static_override: bool | None = False if not static_analysis else None

        try:
            run_assessment(
                repo=repo,
                output_directory=output,
                mode=mode,
                model_id=model_id,
                branch=branch,
                report_title=report_title,
                organization_name=organization_name,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                max_context_characters=max_context_characters,
                include_raw_model_response=include_raw_model_response,
                pmd_path=pmd_path,
                pmd_profile=pmd_profile,
                static_analysis_enabled=static_override,
                config_path=config,
                verbose=verbose,
            )
        except AssessmentCommandError as error:
            typer.secho(str(error), fg=typer.colors.RED, err=True)
            if verbose:
                typer.secho(traceback.format_exc(), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=error.exit_code) from error
        except Exception as error:  # noqa: BLE001 - CLI boundary
            typer.secho(
                sanitize_provider_text(str(error)),
                fg=typer.colors.RED,
                err=True,
            )
            if verbose:
                typer.secho(traceback.format_exc(), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from error
