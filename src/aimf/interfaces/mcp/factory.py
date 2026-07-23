"""Composition helpers for the CodeStrata FastMCP server."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from mcp.server.fastmcp import FastMCP

from aimf.application.agents import AgentOrchestrator, create_agent_orchestrator
from aimf.application.assessment import AssessmentApplicationService
from aimf.application.knowledge.ports import KnowledgeStore
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.config import AimfSettings, load_settings
from aimf.infrastructure.knowledge_store.factory import (
    create_knowledge_query_service,
    create_knowledge_store,
)
from aimf.interfaces.mcp.server import build_mcp_server


def create_mcp_server(
    *,
    query_service: KnowledgeQueryService | None = None,
    assessment_service: AssessmentApplicationService | None = None,
    settings: AimfSettings | None = None,
    config_path: Path | None = None,
    knowledge_store: KnowledgeStore | None = None,
    agent_orchestrator: AgentOrchestrator | None = None,
    incremental_planning_service: object | None = None,
    incremental_execution_service: object | None = None,
    incremental_inspection_service: object | None = None,
    enterprise_knowledge_service: object | None = None,
    enterprise_query_service: object | None = None,
    rule_analysis_service: object | None = None,
) -> FastMCP:
    """Create a CodeStrata FastMCP server with injectable application services.

    Importing this module has no side effects. Store/Bedrock connections occur
    only when services are constructed here or when tools execute.
    """

    resolved_settings = settings
    if resolved_settings is None and config_path is not None:
        resolved_settings = load_settings(config_path)

    queries = query_service
    if queries is None:
        if knowledge_store is not None:
            queries = KnowledgeQueryService(knowledge_store)
        else:
            queries = create_knowledge_query_service(settings=resolved_settings)

    assess = assessment_service or AssessmentApplicationService()
    orchestrator = agent_orchestrator
    if orchestrator is None:
        orchestrator = create_agent_orchestrator(
            query_service=queries,
            assessment_service=assess,
            settings=resolved_settings,
        )

    operations = incremental_execution_service
    inspection = incremental_inspection_service
    if operations is None and resolved_settings is not None:
        from aimf.application.incremental.factory import (
            AssessmentApplicationServiceRunner,
            create_incremental_operations_service,
            create_incremental_planning_service,
        )
        from aimf.application.incremental.inspection import IncrementalInspectionService
        from aimf.application.incremental.provenance import (
            FileIncrementalExecutionRecordStore,
        )

        planning = incremental_planning_service or create_incremental_planning_service(
            query_service=queries,
            settings=resolved_settings,
        )
        runner = AssessmentApplicationServiceRunner(
            assess,
            knowledge_store=knowledge_store,
            config_path=config_path or Path("aimf.toml"),
        )
        operations = create_incremental_operations_service(
            assessment_runner=runner,
            query_service=queries,
            planning_service=planning,  # type: ignore[arg-type]
            settings=resolved_settings,
        )
        if inspection is None:
            store = FileIncrementalExecutionRecordStore(
                Path(resolved_settings.knowledge.directory) / "incremental_executions"
            )
            inspection = IncrementalInspectionService(store)

    enterprise_knowledge = enterprise_knowledge_service
    enterprise_queries = enterprise_query_service
    if enterprise_knowledge is None and resolved_settings is not None:
        from aimf.application.enterprise.factory import (
            create_enterprise_knowledge_service,
            create_enterprise_query_service,
            policy_from_settings,
        )

        policy = policy_from_settings(resolved_settings).model_copy(
            update={
                "allow_unresolved_repositories": True,
                "require_registered_repositories": False,
            }
        )
        enterprise_knowledge = create_enterprise_knowledge_service(
            settings=resolved_settings,
            policy=policy,
        )
        if enterprise_queries is None:
            enterprise_queries = create_enterprise_query_service(
                settings=resolved_settings,
                policy=policy,
            )

    rules_service = rule_analysis_service
    if rules_service is None:
        from aimf.application.rules.factory import create_rule_analysis_service

        rules_service = create_rule_analysis_service(settings=resolved_settings)

    return build_mcp_server(
        queries=queries,
        assessment_service=assess,
        settings=resolved_settings,
        agent_orchestrator=orchestrator,
        incremental_operations=operations,
        incremental_inspection=inspection,
        enterprise_knowledge_service=enterprise_knowledge,
        enterprise_query_service=enterprise_queries,
        rule_analysis_service=rules_service,
    )


def open_default_knowledge_store(settings: AimfSettings) -> KnowledgeStore:
    """Open the configured SQLite knowledge store for MCP composition."""

    store = create_knowledge_store(settings=settings)
    store.open()
    return cast(KnowledgeStore, store)
