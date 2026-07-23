"""Application-layer orchestration for modernization assessment."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from rich.console import Console

from aimf.ai.providers.parsing import sanitize_provider_text
from aimf.application.knowledge.errors import KnowledgeStoreError
from aimf.application.knowledge.ports import KnowledgeStore
from aimf.application.knowledge.session import AssessmentKnowledgeSession
from aimf.config import AimfSettings, configured_repository_source, load_settings
from aimf.config.settings import (
    is_github_repository_source as is_github_repository_source_settings,
)
from aimf.models import AnalysisResult, Repository
from aimf.reporters.report_paths import (
    ReportPaths,
    create_report_paths,
    format_report_run_timestamp,
    prune_excess_report_runs,
)
from aimf.reporting import (
    AssessmentMode,
    AssessmentTiming,
    ModernizationReportInput,
    ModernizationReportValidationError,
    write_modernization_assessment_reports,
)
from aimf.reporting.ai_execution import (
    AI_EXECUTION_FILENAME,
    build_ai_execution_document,
    try_write_ai_execution_artifact,
)
from aimf.reporting.ai_status import (
    attempt_info_from_metadata,
    customer_failure_message,
    failure_code_for_status,
    stages_for_status,
)
from aimf.reporting.modernization_models import AIAttemptInfo, AIExecutionStatus
from aimf.repository_auth.exceptions import (
    RepositoryAccessError,
    UnsupportedRepositoryUrlError,
)
from aimf.services.analysis_service import AnalysisService
from aimf.services.default_pipeline import create_default_analysis_service
from aimf.services.graph_assessment import (
    GraphArtifactWriteResult,
    GraphAssessmentPipeline,
    GraphAssessmentPipelineError,
    format_graph_console_summary,
    write_graph_artifacts,
)
from aimf.services.recommendations import (
    RecommendationEngine,
    RecommendationsArtifactWriteResult,
    write_recommendations_artifact,
)
from aimf.services.rule_engine import (
    FindingsArtifactWriteResult,
    RuleEngine,
    format_rule_console_summary,
    write_findings_artifact,
)
from aimf.services.scanners.github_repository_scanner import GitHubRepositoryScanner
from aimf.services.scanners.local_repository_scanner import LocalRepositoryScanner
from aimf.static_analysis.exceptions import StaticAnalysisProviderError
from aimf.static_analysis.models import StaticAnalysisStatus
from aimf.static_analysis.providers.pmd_discovery import (
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
    from aimf.domain.ai_enrichment import AiEnrichmentResult

DEFAULT_ASSESS_OUTPUT_DIRECTORY = Path("reports")
DEFAULT_ASSESS_REPORT_TITLE = "Modernization Assessment"
DEFAULT_ASSESS_TEMPERATURE = 0.0
DEFAULT_ASSESS_MAX_OUTPUT_TOKENS = 5000
AIMF_BEDROCK_MODEL_ID_ENV = "AIMF_BEDROCK_MODEL_ID"


class AssessmentCommandError(Exception):
    """Assessment failure raised by the application layer."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = 1,
        ai_status: AIExecutionStatus | None = None,
        ai_attempt: AIAttemptInfo | None = None,
        execution_document: dict[str, object] | None = None,
        customer_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.ai_status = ai_status
        self.ai_attempt = ai_attempt
        self.execution_document = execution_document
        self.customer_message = customer_message


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
    graphs_directory: Path | None = None
    knowledge_binding_count: int | None = Field(default=None, ge=0)
    repository_graph_node_count: int | None = Field(default=None, ge=0)
    repository_graph_relationship_count: int | None = Field(default=None, ge=0)
    assessment_graph_node_count: int | None = Field(default=None, ge=0)
    assessment_graph_relationship_count: int | None = Field(default=None, ge=0)
    rule_finding_count: int | None = Field(default=None, ge=0)
    rules_evaluated_count: int | None = Field(default=None, ge=0)
    findings_artifact_path: Path | None = None
    phase3_recommendation_count: int | None = Field(default=None, ge=0)
    recommendations_artifact_path: Path | None = None
    knowledge_repository_id: str | None = None
    knowledge_run_id: str | None = None
    knowledge_snapshot_id: str | None = None

    @model_validator(mode="after")
    def populate_report_path_alias(self) -> AssessmentCommandResult:
        if self.report_path is None:
            return self.model_copy(update={"report_path": self.html_report_path})
        return self


class _RepositoryScanner(Protocol):
    def scan(self, source: str | Path) -> Repository:
        """Scan a repository source and return repository metadata."""


class AssessmentApplicationService:
    """Coordinate end-to-end modernization assessment for any entrypoint.

    Owns orchestration only: repository preparation, scanning, deterministic
    analysis, graphs, rules, recommendations, optional AI enrichment, report
    generation, artifact persistence, and execution status. Business logic
    remains in existing domain and service modules.

    This service must not import Typer or other CLI adapters.
    """

    def run(
        self,
        repo: str | None,
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
        graph_pipeline: GraphAssessmentPipeline | None = None,
        rule_engine: RuleEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        console: Console | None = None,
        clock: Callable[[], datetime] | None = None,
        verbose: bool = False,
        knowledge_store: KnowledgeStore | None = None,
    ) -> AssessmentCommandResult:
        """Orchestrate scan → analysis → graph pipeline → optional AI → HTML+JSON reports.

        Repository selection precedence:

        1. Explicit ``repo`` / ``--repo`` argument
        2. ``[repository].path`` from configuration
        3. ``[repository].url`` from configuration
        4. Clear actionable error (never a silent demo repository)
        """

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

        resolved_repo = resolve_assessment_repository(repo, loaded_settings)
        resolved_branch = branch if branch is not None else loaded_settings.repository.branch
        repository_reference = _safe_repository_reference(resolved_repo)

        stage("Scanning repository")
        scan_started = perf_counter()
        try:
            repository = _scan_repository(
                resolved_repo,
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

        from aimf.infrastructure.knowledge_store.factory import create_knowledge_store
        from aimf.infrastructure.knowledge_store.git_revision import (
            observe_repository_revision,
        )

        owned_store = False
        active_knowledge_store: KnowledgeStore
        if knowledge_store is None:
            active_knowledge_store = cast(
                KnowledgeStore,
                create_knowledge_store(settings=loaded_settings),
            )
            owned_store = True
        else:
            active_knowledge_store = knowledge_store

        try:
            with AssessmentKnowledgeSession(
                store=active_knowledge_store,
                repository=repository,
                mode=mode,
                owns_store=owned_store,
                revision_observer=observe_repository_revision,
            ) as knowledge_session:
                try:
                    return self._run_assessment_pipeline(
                        repository=repository,
                        loaded_settings=loaded_settings,
                        mode=mode,
                        model_id=model_id,
                        resolved_branch=resolved_branch,
                        report_title=report_title,
                        organization_name=organization_name,
                        max_output_tokens=max_output_tokens,
                        temperature=temperature,
                        max_context_characters=max_context_characters,
                        pmd_path=pmd_path,
                        pmd_profile=pmd_profile,
                        static_analysis_enabled=static_analysis_enabled,
                        analysis_service=analysis_service,
                        provider=provider,
                        prompt_builder=prompt_builder,
                        agent=agent,
                        context_builder=context_builder,
                        graph_pipeline=graph_pipeline,
                        rule_engine=rule_engine,
                        recommendation_engine=recommendation_engine,
                        output_directory=output_directory,
                        repository_reference=repository_reference,
                        scan_ms=scan_ms,
                        total_started=total_started,
                        active_console=active_console,
                        now=now,
                        stage=stage,
                        warn=warn,
                        verbose=verbose,
                        knowledge_session=knowledge_session,
                    )
                except AssessmentCommandError as error:
                    knowledge_session.fail(
                        error_code="ASSESSMENT_FAILED",
                        error_message=sanitize_provider_text(str(error)),
                    )
                    raise
                except Exception as error:  # noqa: BLE001 - application boundary
                    knowledge_session.fail(
                        error_code="ASSESSMENT_FAILED",
                        error_message=sanitize_provider_text(str(error)),
                    )
                    raise
        except KnowledgeStoreError as error:
            raise AssessmentCommandError(
                f"Knowledge store failure: {sanitize_provider_text(str(error))}"
            ) from error



    def _run_assessment_pipeline(
        self,
        *,
        repository: Repository,
        loaded_settings: AimfSettings,
        mode: AssessmentMode,
        model_id: str | None,
        resolved_branch: str | None,
        report_title: str,
        organization_name: str | None,
        max_output_tokens: int,
        temperature: float,
        max_context_characters: int | None,
        pmd_path: str | None,
        pmd_profile: str | None,
        static_analysis_enabled: bool | None,
        analysis_service: AnalysisService | None,
        provider: AIModelProvider | None,
        prompt_builder: ModernizationPromptBuilder | None,
        agent: ModernizationAssessmentAgent | None,
        context_builder: LLMAnalysisContextBuilder | None,
        graph_pipeline: GraphAssessmentPipeline | None,
        rule_engine: RuleEngine | None,
        recommendation_engine: RecommendationEngine | None,
        output_directory: Path,
        repository_reference: str,
        scan_ms: float,
        total_started: float,
        active_console: Console,
        now: Callable[[], datetime],
        stage: Callable[[str], None],
        warn: Callable[[str], None],
        verbose: bool,
        knowledge_session: AssessmentKnowledgeSession,
    ) -> AssessmentCommandResult:
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
        except Exception as error:  # noqa: BLE001 - application boundary
            raise AssessmentCommandError(
                f"Deterministic analysis failed: {sanitize_provider_text(str(error))}"
            ) from error
        analysis_ms = round((perf_counter() - analysis_started) * 1000, 2)

        static_analysis_ms = _static_analysis_duration_ms(analysis_result)
        warnings = _static_analysis_warnings(analysis_result)
        for message in warnings:
            warn(message)
        _print_static_analysis_success(active_console, analysis_result)

        stage("Building knowledge graphs")
        graph_started = perf_counter()
        active_graph_pipeline = graph_pipeline or GraphAssessmentPipeline()
        try:
            graph_pipeline_result = active_graph_pipeline.run(repository)
        except GraphAssessmentPipelineError as error:
            raise AssessmentCommandError(sanitize_provider_text(str(error))) from error
        except Exception as error:  # noqa: BLE001 - application boundary
            raise AssessmentCommandError(
                f"[graph_pipeline] Graph assessment pipeline failed: "
                f"{sanitize_provider_text(str(error))}"
            ) from error

        # Create the run directory before AI so graph artifacts persist even when AI fails.
        generated_at = now()
        run_timestamp = format_report_run_timestamp(generated_at)
        report_paths = create_report_paths(
            analysis_result,
            output_directory,
            timestamp=run_timestamp,
            create_directory=True,
        )
        try:
            graph_artifacts = write_graph_artifacts(
                graph_pipeline_result,
                report_paths.run_directory,
            )
        except GraphAssessmentPipelineError as error:
            raise AssessmentCommandError(sanitize_provider_text(str(error))) from error
        graph_elapsed_ms = round((perf_counter() - graph_started) * 1000, 2)
        _ = graph_elapsed_ms
        for line in format_graph_console_summary(graph_artifacts.summary):
            active_console.print(line)

        stage("Evaluating assessment rules")
        active_rule_engine = rule_engine or RuleEngine()
        active_recommendation_engine = recommendation_engine or RecommendationEngine()
        try:
            rule_evaluation = active_rule_engine.evaluate_pipeline_result(graph_pipeline_result)
            findings_artifact = write_findings_artifact(
                rule_evaluation,
                report_paths.run_directory,
            )
        except Exception as error:  # noqa: BLE001 - application boundary
            raise AssessmentCommandError(
                f"[rule_engine] Rule evaluation failed: {sanitize_provider_text(str(error))}"
            ) from error
        try:
            recommendation_result = active_recommendation_engine.evaluate_pipeline_result(
                pipeline_result=graph_pipeline_result,
                evaluation=rule_evaluation,
            )
            recommendations_artifact = write_recommendations_artifact(
                recommendation_result,
                report_paths.run_directory,
            )
        except Exception as error:  # noqa: BLE001 - application boundary
            raise AssessmentCommandError(
                f"[recommendation_engine] Recommendation evaluation failed: "
                f"{sanitize_provider_text(str(error))}"
            ) from error
        for line in format_rule_console_summary(
            rule_evaluation,
            recommendation_count=recommendation_result.recommendation_count,
        ):
            active_console.print(line)

        analysis_context: LLMAnalysisContext | None = None
        assessment_result: ModernizationAssessmentResult | None = None
        ai_ms: float | None = None
        ai_status = AIExecutionStatus.NOT_REQUESTED
        ai_failure_message: str | None = None
        ai_attempt: AIAttemptInfo | None = None
        ai_execution_document: dict[str, object] | None = None
        enrichment_result: AiEnrichmentResult | None = None

        if mode == AssessmentMode.AI_ENHANCED:
            from aimf.ai.enrichment import DEFAULT_MAX_CONTEXT_CHARACTERS
            from aimf.ai.enrichment.artifacts import (
                AI_ENRICHMENT_FILENAME,
                try_write_ai_enrichment_artifact,
            )

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
            try:
                (
                    analysis_context,
                    assessment_result,
                    ai_attempt,
                    enrichment_result,
                ) = _run_ai_assessment(
                    analysis_result=analysis_result,
                    settings=loaded_settings,
                    resolved_model_id=resolved_model_id,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    context_limit=context_limit,
                    provider=provider,
                    prompt_builder=prompt_builder,
                    agent=agent,
                    context_builder=context_builder,
                    rule_evaluation=rule_evaluation,
                    recommendation_result=recommendation_result,
                    repository_graph=graph_pipeline_result.repository_graph,
                    stage=stage,
                )
                ai_status = AIExecutionStatus.SUCCEEDED
                ai_execution_document = build_ai_execution_document(
                    status=AIExecutionStatus.SUCCEEDED,
                    attempt=ai_attempt,
                    analysis_context=analysis_context,
                    assessment_result=assessment_result,
                    failure_message=None,
                )
                if enrichment_result is not None:
                    written_enrichment = try_write_ai_enrichment_artifact(
                        enrichment_result,
                        report_paths.run_directory,
                    )
                    if written_enrichment is None:
                        warn(
                            "AI enrichment artifact could not be written; "
                            "customer HTML and JSON reports were kept. "
                            f"Expected file: {AI_ENRICHMENT_FILENAME}"
                        )
            except AssessmentCommandError as error:
                ai_status = error.ai_status or AIExecutionStatus.PROVIDER_FAILED
                ai_attempt = error.ai_attempt
                ai_execution_document = error.execution_document
                ai_failure_message = error.customer_message or customer_failure_message(ai_status)
                detail = sanitize_provider_text(str(error))
                if ai_attempt is not None and ai_attempt.failure_detail is None:
                    ai_attempt = ai_attempt.model_copy(update={"failure_detail": detail})
                elif ai_attempt is None:
                    ai_attempt = AIAttemptInfo(
                        model_id=resolved_model_id,
                        stages_completed=stages_for_status(ai_status),
                        failure_code=failure_code_for_status(ai_status),
                        failure_detail=detail,
                    )
                code = failure_code_for_status(ai_status) or "AI_FAILED"
                warnings.append(
                    f"{ai_failure_message} [{code}] "
                    "Deterministic HTML and JSON reports were still written."
                )
                warn(warnings[-1])
                if analysis_context is None:
                    try:
                        from aimf.ai.contracts import LLMAnalysisContextBuilder

                        analysis_context = (context_builder or LLMAnalysisContextBuilder()).build(
                            analysis_result
                        )
                    except Exception:  # noqa: BLE001 - best effort only
                        analysis_context = None
                if ai_execution_document is None:
                    ai_execution_document = build_ai_execution_document(
                        status=ai_status,
                        attempt=ai_attempt,
                        analysis_context=analysis_context,
                        raw_model_text=None,
                        parsed_model_response=None,
                        accepted_ai_result=None,
                        failure_message=ai_failure_message,
                        failure_detail=(
                            ai_attempt.failure_detail if ai_attempt is not None else None
                        ),
                    )
            ai_ms = round((perf_counter() - ai_started) * 1000, 2)
            if ai_attempt is not None and ai_attempt.latency_ms is None and ai_ms is not None:
                ai_attempt = ai_attempt.model_copy(update={"latency_ms": ai_ms})

        stage("Generating HTML and JSON reports")
        # Reuse the run directory created before optional AI so graph artifacts remain
        # alongside HTML/JSON for the same assessment run.
        from aimf.reporting.html_v2 import build_highlighted_versions, default_report_artifacts

        generated_at = now()
        provisional_total = round((perf_counter() - total_started) * 1000, 2)
        include_ai_enrichment = (
            enrichment_result is not None and ai_status == AIExecutionStatus.SUCCEEDED
        )
        report_input = ModernizationReportInput(
            analysis_result=analysis_result,
            assessment_mode=mode,
            analysis_context=analysis_context,
            assessment_result=assessment_result,
            ai_status=ai_status,
            ai_failure_message=ai_failure_message,
            ai_attempt=ai_attempt,
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
            assessment_rule_evaluation=rule_evaluation,
            assessment_recommendation_result=recommendation_result,
            ai_enrichment=enrichment_result if include_ai_enrichment else None,
            highlighted_versions=build_highlighted_versions(graph_pipeline_result.repository_graph),
            report_artifacts=default_report_artifacts(
                include_ai_enrichment=include_ai_enrichment,
                include_ai_execution=ai_execution_document is not None,
            ),
        )

        try:
            written_paths = write_modernization_assessment_reports(
                report_input,
                report_paths,
            )
            if ai_execution_document is not None:
                written = try_write_ai_execution_artifact(
                    written_paths.run_directory,
                    ai_execution_document,
                )
                if written is None:
                    warn(
                        "AI execution artifact could not be written; "
                        "customer HTML and JSON reports were kept. "
                        f"Expected file: {AI_EXECUTION_FILENAME}"
                    )
        except ModernizationReportValidationError as error:
            raise AssessmentCommandError(
                f"Report validation or write failure: {sanitize_provider_text(str(error))}"
            ) from error
        except OSError as error:
            raise AssessmentCommandError(
                f"Report validation or write failure: {sanitize_provider_text(str(error))}"
            ) from error
        except Exception as error:  # noqa: BLE001 - application boundary
            raise AssessmentCommandError(
                f"Report validation or write failure: {sanitize_provider_text(str(error))}"
            ) from error

        try:
            deleted = prune_excess_report_runs(written_paths.run_directory.parent)
            if deleted:
                for path in deleted:
                    active_console.print(f"Removed aged report run: {path.name}")
        except Exception as error:  # noqa: BLE001 - retention must not fail assessment
            warn(
                "Report retention cleanup failed; the current assessment reports were kept. "
                f"Details: {sanitize_provider_text(str(error))}"
            )

        total_ms = round((perf_counter() - total_started) * 1000, 2)

        result = _build_command_result(
            repository_name=repository.name,
            report_paths=written_paths,
            mode=mode,
            analysis_result=analysis_result,
            assessment_result=assessment_result,
            ai_status=ai_status,
            ai_attempt=ai_attempt,
            duration_ms=total_ms,
            graph_artifacts=graph_artifacts,
            rule_evaluation=rule_evaluation,
            findings_artifact=findings_artifact,
            recommendation_result=recommendation_result,
            recommendations_artifact=recommendations_artifact,
        )
        _print_success_summary(active_console, result)
        try:
            snapshot_id = knowledge_session.complete(
                graph_pipeline_result=graph_pipeline_result,
                rule_evaluation=rule_evaluation,
                recommendation_result=recommendation_result,
                ai_execution_document=ai_execution_document,
                enrichment_result=enrichment_result,
                configured_branch=resolved_branch,
            )
        except KnowledgeStoreError as error:
            raise AssessmentCommandError(
                f"Knowledge persistence failed: {sanitize_provider_text(str(error))}"
            ) from error
        except Exception as error:  # noqa: BLE001 - application boundary
            raise AssessmentCommandError(
                f"Knowledge persistence failed: {sanitize_provider_text(str(error))}"
            ) from error

        return result.model_copy(
            update={
                "knowledge_repository_id": knowledge_session.repository_id,
                "knowledge_run_id": knowledge_session.run_id,
                "knowledge_snapshot_id": snapshot_id,
            }
        )


def run_assessment(
    repo: str | None,
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
    graph_pipeline: GraphAssessmentPipeline | None = None,
    rule_engine: RuleEngine | None = None,
    recommendation_engine: RecommendationEngine | None = None,
        console: Console | None = None,
        clock: Callable[[], datetime] | None = None,
        verbose: bool = False,
        knowledge_store: KnowledgeStore | None = None,
) -> AssessmentCommandResult:
    """Orchestrate scan → analysis → graph pipeline → optional AI → HTML+JSON reports.

    Repository selection precedence:

    1. Explicit ``repo`` / ``--repo`` argument
    2. ``[repository].path`` from configuration
    3. ``[repository].url`` from configuration
    4. Clear actionable error (never a silent demo repository)
    """

    return AssessmentApplicationService().run(
        repo,
        output_directory,
        mode=mode,
        model_id=model_id,
        branch=branch,
        report_title=report_title,
        organization_name=organization_name,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        max_context_characters=max_context_characters,
        pmd_path=pmd_path,
        pmd_profile=pmd_profile,
        static_analysis_enabled=static_analysis_enabled,
        config_path=config_path,
        settings=settings,
        analysis_service=analysis_service,
        provider=provider,
        prompt_builder=prompt_builder,
        agent=agent,
        scanner=scanner,
        context_builder=context_builder,
        graph_pipeline=graph_pipeline,
        rule_engine=rule_engine,
        recommendation_engine=recommendation_engine,
        console=console,
        clock=clock,
        verbose=verbose,
        knowledge_store=knowledge_store,
    )


def resolve_bedrock_model_id(
    *,
    cli_model_id: str | None,
    settings: AimfSettings,
) -> str:
    """Resolve Bedrock model ID from CLI, environment, config, then default."""

    from aimf.config.settings import DEFAULT_BEDROCK_MODEL_ID

    if cli_model_id and cli_model_id.strip():
        return cli_model_id.strip()

    env_model_id = os.environ.get(AIMF_BEDROCK_MODEL_ID_ENV)
    if env_model_id and env_model_id.strip():
        return env_model_id.strip()

    configured = settings.ai.bedrock.model_id
    if configured and configured.strip():
        return configured.strip()

    return DEFAULT_BEDROCK_MODEL_ID


def modernization_report_basename(repository_name: str) -> str:
    """Return a sanitized assessment report basename (without extension)."""

    return f"{_slugify(repository_name)}-modernization-assessment"


def modernization_report_filename(repository_name: str) -> str:
    """Return a sanitized HTML report filename for a repository."""

    return f"{modernization_report_basename(repository_name)}.html"


def modernization_json_report_filename(repository_name: str) -> str:
    """Return a sanitized JSON report filename for a repository."""

    return f"{modernization_report_basename(repository_name)}.json"


def resolve_assessment_repository(
    cli_repo: str | None,
    settings: AimfSettings,
) -> str:
    """Resolve the repository source for ``aimf assess``.

    Precedence: explicit CLI ``--repo``, then ``repository.path``, then
    ``repository.url``. Never falls back to a hardcoded demo repository.
    """

    if cli_repo is not None and cli_repo.strip():
        return cli_repo.strip()

    configured = configured_repository_source(settings)
    if configured:
        return configured

    raise AssessmentCommandError(
        "No repository configured.\n\n"
        "Fix one of the following:\n"
        "  1. Pass --repo /path/to/repository (local path or GitHub URL)\n"
        "  2. Set [repository].path in aimf.toml for a local checkout\n"
        "  3. Set [repository].url in aimf.toml for a GitHub repository\n\n"
        "Examples:\n"
        "  aimf assess --repo /path/to/repository\n"
        "  aimf assess --config aimf.toml"
    )


def is_github_repository_source(repo: str) -> bool:
    """Return whether the repo argument is a GitHub URL."""

    return is_github_repository_source_settings(repo)


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
    provider: AIModelProvider | None,
    prompt_builder: ModernizationPromptBuilder | None,
    agent: ModernizationAssessmentAgent | None,
    context_builder: LLMAnalysisContextBuilder | None,
    rule_evaluation: object,
    recommendation_result: object,
    repository_graph: object | None,
    stage: Callable[[str], None],
) -> tuple[
    LLMAnalysisContext,
    ModernizationAssessmentResult,
    AIAttemptInfo,
    AiEnrichmentResult,
]:
    from aimf.ai.enrichment import (
        AiEnrichmentPromptBuilder,
        AiEnrichmentPromptOptions,
        AiEnrichmentService,
    )
    from aimf.ai.enrichment.context import (
        AiEnrichmentBudgetError,
        AiEnrichmentContextLimits,
    )
    from aimf.ai.enrichment.prompt import AiEnrichmentPromptBuildError
    from aimf.ai.providers.exceptions import (
        AIProviderError,
        AIProviderTimeoutError,
        AIResponseParsingError,
        AIResponseValidationError,
    )
    from aimf.ai.providers.models import ModelInvocationOptions
    from aimf.domain.findings import RuleEvaluationResult
    from aimf.domain.recommendations import RecommendationResult
    from aimf.domain.repository_graph import RepositoryGraph

    _ = prompt_builder  # Phase 1 prompt builder unused; enrichment has its own prompt.
    _ = agent  # Legacy agent path replaced by single-call enrichment service.

    stage("Building AI enrichment context")
    try:
        active_provider = provider or _create_bedrock_provider(settings)
    except AIProviderError as error:
        raise _map_provider_error(error, model_id=resolved_model_id) from error

    if not isinstance(rule_evaluation, RuleEvaluationResult):
        raise AssessmentCommandError(
            "AI enrichment requires RuleEvaluationResult",
            ai_status=AIExecutionStatus.PROVIDER_FAILED,
            customer_message=customer_failure_message(AIExecutionStatus.PROVIDER_FAILED),
        )
    if not isinstance(recommendation_result, RecommendationResult):
        raise AssessmentCommandError(
            "AI enrichment requires RecommendationResult",
            ai_status=AIExecutionStatus.PROVIDER_FAILED,
            customer_message=customer_failure_message(AIExecutionStatus.PROVIDER_FAILED),
        )
    graph = repository_graph if isinstance(repository_graph, RepositoryGraph) else None

    stage("Running AI enrichment")
    service = AiEnrichmentService(
        active_provider,
        prompt_builder=AiEnrichmentPromptBuilder(),
        context_builder=context_builder,
    )
    model_options = ModelInvocationOptions(
        model_id=resolved_model_id,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    prompt_options = AiEnrichmentPromptOptions(max_context_characters=context_limit)
    context_limits = AiEnrichmentContextLimits(max_context_characters=context_limit)

    try:
        run = service.run(
            analysis_result=analysis_result,
            rule_evaluation=rule_evaluation,
            recommendation_result=recommendation_result,
            repository_graph=graph,
            model_options=model_options,
            context_limits=context_limits,
            prompt_options=prompt_options,
        )
    except AiEnrichmentBudgetError as error:
        raise AssessmentCommandError(
            f"AI enrichment context budget failure: {sanitize_provider_text(str(error))}",
            ai_status=AIExecutionStatus.PROVIDER_FAILED,
            customer_message=customer_failure_message(AIExecutionStatus.PROVIDER_FAILED),
            ai_attempt=AIAttemptInfo(
                model_id=resolved_model_id,
                stages_completed=stages_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_code=failure_code_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_detail=sanitize_provider_text(str(error)),
            ),
        ) from error
    except AiEnrichmentPromptBuildError as error:
        raise AssessmentCommandError(
            f"AI enrichment prompt failure: {sanitize_provider_text(str(error))}",
            ai_status=AIExecutionStatus.PROVIDER_FAILED,
            customer_message=customer_failure_message(AIExecutionStatus.PROVIDER_FAILED),
            ai_attempt=AIAttemptInfo(
                model_id=resolved_model_id,
                stages_completed=stages_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_code=failure_code_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_detail=sanitize_provider_text(str(error)),
            ),
        ) from error
    except AIProviderTimeoutError as error:
        raise AssessmentCommandError(
            f"Bedrock timeout or throttling: {sanitize_provider_text(str(error))}",
            ai_status=AIExecutionStatus.PROVIDER_FAILED,
            customer_message=customer_failure_message(AIExecutionStatus.PROVIDER_FAILED),
            ai_attempt=AIAttemptInfo(
                provider="bedrock",
                model_id=resolved_model_id,
                stages_completed=stages_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_code=failure_code_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_detail=sanitize_provider_text(str(error)),
            ),
        ) from error
    except (AIResponseValidationError, AIResponseParsingError) as error:
        raise _map_response_contract_error(error, model_id=resolved_model_id) from error
    except AIProviderError as error:
        raise _map_provider_error(error, model_id=resolved_model_id) from error
    except Exception as error:  # noqa: BLE001 - application boundary
        raise AssessmentCommandError(
            f"AI enrichment failed: {sanitize_provider_text(str(error))}",
            ai_status=AIExecutionStatus.PROVIDER_FAILED,
            customer_message=customer_failure_message(AIExecutionStatus.PROVIDER_FAILED),
            ai_attempt=AIAttemptInfo(
                model_id=resolved_model_id,
                stages_completed=stages_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_code=failure_code_for_status(AIExecutionStatus.PROVIDER_FAILED),
                failure_detail=sanitize_provider_text(str(error)),
            ),
        ) from error

    attempt = attempt_info_from_metadata(
        run.assessment_result.model_metadata,
        status=AIExecutionStatus.SUCCEEDED,
    )
    enrichment: AiEnrichmentResult = run.enrichment
    return run.analysis_context, run.assessment_result, attempt, enrichment


def _map_response_contract_error(
    error: Exception,
    *,
    model_id: str,
) -> AssessmentCommandError:
    from aimf.ai.providers.exceptions import AIResponseValidationError

    status = (
        AIExecutionStatus.VALIDATION_FAILED
        if isinstance(error, AIResponseValidationError)
        else AIExecutionStatus.PARSING_FAILED
    )
    metadata = getattr(error, "metadata", None)
    raw_text = getattr(error, "raw_response_text", None)
    parsed_payload = getattr(error, "parsed_payload", None)
    validation_details = getattr(error, "validation_details", None) or str(error)
    detail = sanitize_provider_text(str(error))
    if metadata is not None:
        attempt = attempt_info_from_metadata(
            metadata,
            status=status,
            failure_detail=detail,
        )
    else:
        attempt = AIAttemptInfo(
            provider="bedrock",
            model_id=model_id,
            stages_completed=stages_for_status(status),
            failure_code=failure_code_for_status(status),
            failure_detail=detail,
        )
    label = "Invalid model response"
    return AssessmentCommandError(
        f"{label}: {detail}",
        ai_status=status,
        customer_message=customer_failure_message(status),
        ai_attempt=attempt,
        execution_document=build_ai_execution_document(
            status=status,
            attempt=attempt,
            raw_model_text=raw_text if isinstance(raw_text, str) else None,
            parsed_model_response=parsed_payload if isinstance(parsed_payload, dict) else None,
            accepted_ai_result=None,
            failure_message=customer_failure_message(status),
            failure_detail=sanitize_provider_text(str(validation_details)),
        ),
    )


def _map_provider_error(
    error: Exception,
    *,
    model_id: str | None = None,
) -> AssessmentCommandError:
    message = sanitize_provider_text(str(error))
    lowered = message.lower()
    is_auth = (
        "unable to authenticate with aws" in lowered
        or "authentication" in lowered
        or "authenticate" in lowered
        or "expired token" in lowered
        or "sso" in lowered
        or "nocredentials" in lowered
    )
    if is_auth and "unable to authenticate with aws" not in lowered:
        from aimf.ai.aws_config import format_aws_authentication_error

        message = format_aws_authentication_error()
        is_auth = True

    if is_auth:
        status = AIExecutionStatus.AUTHENTICATION_FAILED
        attempt = AIAttemptInfo(
            provider="bedrock",
            model_id=model_id,
            stages_completed=stages_for_status(status),
            failure_code=failure_code_for_status(status),
            failure_detail=message,
        )
        return AssessmentCommandError(
            message,
            ai_status=status,
            customer_message=customer_failure_message(status),
            ai_attempt=attempt,
            execution_document=build_ai_execution_document(
                status=status,
                attempt=attempt,
                accepted_ai_result=None,
                failure_message=customer_failure_message(status),
                failure_detail=message,
            ),
        )

    status = AIExecutionStatus.PROVIDER_FAILED
    if "model access denied" in lowered or "invalid model or request configuration" in lowered:
        detail = message
    elif (
        "throttl" in lowered
        or "timed out" in lowered
        or "timeout" in lowered
        or "temporary service failure" in lowered
    ):
        detail = f"Bedrock timeout or throttling: {message}"
    else:
        detail = f"Model provider failure: {message}"
    attempt = AIAttemptInfo(
        provider="bedrock",
        model_id=model_id,
        stages_completed=stages_for_status(status),
        failure_code=failure_code_for_status(status),
        failure_detail=detail,
    )
    return AssessmentCommandError(
        detail,
        ai_status=status,
        customer_message=customer_failure_message(status),
        ai_attempt=attempt,
        execution_document=build_ai_execution_document(
            status=status,
            attempt=attempt,
            accepted_ai_result=None,
            failure_message=customer_failure_message(status),
            failure_detail=detail,
        ),
    )


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
    ai_status: AIExecutionStatus,
    ai_attempt: AIAttemptInfo | None,
    duration_ms: float | None,
    graph_artifacts: GraphArtifactWriteResult | None = None,
    rule_evaluation: object | None = None,
    findings_artifact: FindingsArtifactWriteResult | None = None,
    recommendation_result: object | None = None,
    recommendations_artifact: RecommendationsArtifactWriteResult | None = None,
) -> AssessmentCommandResult:
    deterministic_recommendation_count = len(analysis_result.recommendations)
    graph_fields: dict[str, object] = {}
    if graph_artifacts is not None:
        summary = graph_artifacts.summary
        graph_fields = {
            "graphs_directory": graph_artifacts.directory,
            "knowledge_binding_count": summary.binding_count,
            "repository_graph_node_count": summary.repository_node_count,
            "repository_graph_relationship_count": summary.repository_relationship_count,
            "assessment_graph_node_count": summary.assessment_node_count,
            "assessment_graph_relationship_count": summary.assessment_relationship_count,
        }
    if rule_evaluation is not None:
        graph_fields["rule_finding_count"] = getattr(rule_evaluation, "finding_count", 0)
        graph_fields["rules_evaluated_count"] = len(getattr(rule_evaluation, "rules_evaluated", ()))
    if findings_artifact is not None:
        graph_fields["findings_artifact_path"] = findings_artifact.path
    if recommendation_result is not None:
        graph_fields["phase3_recommendation_count"] = getattr(
            recommendation_result,
            "recommendation_count",
            0,
        )
    if recommendations_artifact is not None:
        graph_fields["recommendations_artifact_path"] = recommendations_artifact.path
    if (
        mode == AssessmentMode.AI_ENHANCED
        and ai_status == AIExecutionStatus.SUCCEEDED
        and assessment_result is not None
    ):
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
            **graph_fields,  # type: ignore[arg-type]
        )

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
        phases_count=0,
        ai_executed=False,
        input_tokens=ai_attempt.input_tokens if ai_attempt is not None else None,
        output_tokens=ai_attempt.output_tokens if ai_attempt is not None else None,
        model_id=ai_attempt.model_id if ai_attempt is not None else None,
        latency_ms=ai_attempt.latency_ms if ai_attempt is not None else None,
        duration_ms=duration_ms,
        **graph_fields,  # type: ignore[arg-type]
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
        raise AssessmentCommandError(
            "Invalid repository path or URL: repository is empty.\n\n"
            "Fix: pass --repo /path/to/repo or configure [repository] in aimf.toml."
        )

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
    if not path.exists():
        raise AssessmentCommandError(
            f"Repository path does not exist: {path}\n\n"
            "Fix: create or clone the repository, update [repository].path in "
            "aimf.toml, or pass a valid --repo path."
        )
    if not path.is_dir():
        raise AssessmentCommandError(
            f"Repository path is not a directory: {path}\n\n"
            "Fix: point --repo or [repository].path at the repository root."
        )
    return LocalRepositoryScanner().scan(path)


def _create_bedrock_provider(settings: AimfSettings) -> AIModelProvider:
    from aimf.ai.providers.bedrock import BedrockAIModelProvider

    return BedrockAIModelProvider(settings=settings)


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
    if result.mode == AssessmentMode.AI_ENHANCED and result.ai_executed:
        mode_label = "AI Enhanced"
    elif result.mode == AssessmentMode.AI_ENHANCED:
        mode_label = "AI requested, deterministic fallback"
    else:
        mode_label = "Deterministic"
    console.print()
    console.print("[green]Modernization assessment completed[/green]")
    console.print(f"Assessment mode: {mode_label}")
    console.print(f"Repository: {result.repository_name}")
    console.print(f"Findings: {result.findings_count}")
    console.print(f"Technologies: {result.technologies_count}")
    console.print(f"Deterministic recommendations: {result.recommendations_count}")
    if result.graphs_directory is not None:
        console.print(f"Graph artifacts: {_display_path(result.graphs_directory)}")
        if result.knowledge_binding_count is not None:
            console.print(f"Knowledge bindings: {result.knowledge_binding_count}")
    if result.rule_finding_count is not None:
        console.print(f"Rule findings: {result.rule_finding_count}")
    if result.findings_artifact_path is not None:
        console.print(f"Findings artifact: {_display_path(result.findings_artifact_path)}")
    if result.phase3_recommendation_count is not None:
        console.print(f"Graph recommendations: {result.phase3_recommendation_count}")
    if result.recommendations_artifact_path is not None:
        console.print(
            f"Recommendations artifact: {_display_path(result.recommendations_artifact_path)}"
        )
    if result.mode == AssessmentMode.AI_ENHANCED and not result.ai_executed:
        console.print("AI status: fallback (validated AI result not included)")
        if result.model_id:
            console.print(f"Model ID: {result.model_id}")
        if result.input_tokens is not None:
            console.print(f"Input tokens: {result.input_tokens}")
        if result.output_tokens is not None:
            console.print(f"Output tokens: {result.output_tokens}")
    if result.ai_executed:
        console.print("AI status: succeeded")
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
