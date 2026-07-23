"""Composable factory for incremental planning and execution services."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aimf.application.incremental.errors import IncrementalDependencyError
from aimf.application.incremental.execution import IncrementalAssessmentExecutor
from aimf.application.incremental.execution_policies import (
    IncrementalExecutionPolicy,
    execution_policy_from_settings,
)
from aimf.application.incremental.policies import (
    IncrementalPlanningPolicy,
    policy_from_settings,
)
from aimf.application.incremental.ports import CandidateManifestProvider
from aimf.application.incremental.selective_scan import SelectiveScanService
from aimf.application.incremental.service import IncrementalPlanningService
from aimf.application.knowledge.ports import KnowledgeStore
from aimf.application.knowledge.queries.service import KnowledgeQueryService
from aimf.config.settings import AimfSettings
from aimf.models import Repository


class AssessmentApplicationServiceRunner:
    """Adapt AssessmentApplicationService to the FullAssessmentRunner port."""

    def __init__(
        self,
        service: Any,
        *,
        knowledge_store: KnowledgeStore | None = None,
        console: Any | None = None,
        config_path: Path = Path("aimf.toml"),
    ) -> None:
        self._service = service
        self._knowledge_store = knowledge_store
        self._console = console
        self._config_path = config_path

    def run_full(
        self,
        *,
        repository: str,
        output_directory: Path,
        branch: str | None,
        with_ai: bool,
        settings: AimfSettings | None,
        scanned_repository: Repository | None = None,
    ) -> Any:
        from aimf.reporting import AssessmentMode

        mode = AssessmentMode.AI_ENHANCED if with_ai else AssessmentMode.DETERMINISTIC
        return self._service.run(
            repository,
            output_directory,
            mode=mode,
            branch=branch,
            config_path=self._config_path,
            settings=settings,
            knowledge_store=self._knowledge_store,
            console=self._console,
            scanned_repository=scanned_repository,
        )


def create_incremental_planning_service(
    *,
    query_service: KnowledgeQueryService | None = None,
    candidate_manifest_provider: CandidateManifestProvider | None = None,
    settings: AimfSettings | None = None,
    policy: IncrementalPlanningPolicy | None = None,
) -> IncrementalPlanningService:
    """Compose an :class:`IncrementalPlanningService`.

    Production composition may omit injected services; tests should inject fakes.
    This factory does not open databases, call Bedrock, or run assessments at
    import time.
    """

    resolved_policy = policy if policy is not None else policy_from_settings(settings)
    if not isinstance(resolved_policy, IncrementalPlanningPolicy):
        raise IncrementalDependencyError("policy must be an IncrementalPlanningPolicy")

    if query_service is None and settings is not None:
        from aimf.infrastructure.knowledge_store import create_knowledge_query_service

        query_service = create_knowledge_query_service(settings=settings)

    return IncrementalPlanningService(
        query_service=query_service,
        candidate_manifest_provider=candidate_manifest_provider,
        policy=resolved_policy,
    )


def create_incremental_assessment_executor(
    *,
    assessment_runner: Any,
    query_service: KnowledgeQueryService | None = None,
    planning_service: IncrementalPlanningService | None = None,
    selective_scan: SelectiveScanService | None = None,
    settings: AimfSettings | None = None,
    policy: IncrementalExecutionPolicy | None = None,
) -> IncrementalAssessmentExecutor:
    """Compose an :class:`IncrementalAssessmentExecutor`.

    Does not open databases or call Bedrock at import time. Tests should inject
    fakes for the assessment runner and query service.
    """

    resolved_policy = policy if policy is not None else execution_policy_from_settings(settings)
    if not isinstance(resolved_policy, IncrementalExecutionPolicy):
        raise IncrementalDependencyError("policy must be an IncrementalExecutionPolicy")

    if query_service is None and settings is not None:
        from aimf.infrastructure.knowledge_store import create_knowledge_query_service

        query_service = create_knowledge_query_service(settings=settings)

    if planning_service is None:
        planning_service = create_incremental_planning_service(
            query_service=query_service,
            settings=settings,
        )

    return IncrementalAssessmentExecutor(
        assessment_runner=assessment_runner,
        planning_service=planning_service,
        query_service=query_service,
        selective_scan=selective_scan,
        settings=settings,
        policy=resolved_policy,
    )


def create_incremental_operations_service(
    *,
    assessment_runner: Any | None = None,
    query_service: KnowledgeQueryService | None = None,
    planning_service: IncrementalPlanningService | None = None,
    executor: IncrementalAssessmentExecutor | None = None,
    settings: AimfSettings | None = None,
    record_store: Any | None = None,
) -> Any:
    """Compose planning + execution + validation + provenance operations."""

    from aimf.application.incremental.operations import IncrementalOperationsService
    from aimf.application.incremental.provenance import (
        FileIncrementalExecutionRecordStore,
        InMemoryIncrementalExecutionRecordStore,
    )
    from aimf.application.incremental.rollout import rollout_policy_from_settings

    planning = planning_service or create_incremental_planning_service(
        query_service=query_service,
        settings=settings,
    )
    resolved_executor = executor
    if resolved_executor is None and assessment_runner is not None:
        resolved_executor = create_incremental_assessment_executor(
            assessment_runner=assessment_runner,
            query_service=query_service,
            planning_service=planning,
            settings=settings,
        )
    store = record_store
    if store is None and settings is not None:
        knowledge_dir = Path(settings.knowledge.directory)
        store = FileIncrementalExecutionRecordStore(knowledge_dir / "incremental_executions")
    if store is None:
        store = InMemoryIncrementalExecutionRecordStore()
    return IncrementalOperationsService(
        planning_service=planning,
        executor=resolved_executor,
        record_store=store,
        rollout=rollout_policy_from_settings(settings),
    )
