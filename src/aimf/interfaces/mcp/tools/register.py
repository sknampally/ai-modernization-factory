"""Register all CodeStrata MCP tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aimf.application.agents import AgentOrchestrator
from aimf.application.assessment import AssessmentApplicationService
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.config import AimfSettings
from aimf.interfaces.mcp.tools.agents import register_agent_tools
from aimf.interfaces.mcp.tools.artifacts import register_artifact_tools
from aimf.interfaces.mcp.tools.assessments import register_assessment_tools
from aimf.interfaces.mcp.tools.components import register_component_tools
from aimf.interfaces.mcp.tools.enterprise import register_enterprise_tools
from aimf.interfaces.mcp.tools.execution import register_execution_tools
from aimf.interfaces.mcp.tools.findings import register_finding_tools
from aimf.interfaces.mcp.tools.incremental import register_incremental_tools
from aimf.interfaces.mcp.tools.recommendations import register_recommendation_tools
from aimf.interfaces.mcp.tools.repositories import register_repository_tools
from aimf.interfaces.mcp.tools.rules import register_rules_tools
from aimf.interfaces.mcp.tools.snapshots import register_snapshot_tools


def register_all_tools(
    server: FastMCP,
    *,
    queries: KnowledgeQueryService,
    assessment_service: AssessmentApplicationService,
    settings: AimfSettings | None,
    agent_orchestrator: AgentOrchestrator | None = None,
    incremental_operations: object | None = None,
    incremental_inspection: object | None = None,
    enterprise_knowledge_service: object | None = None,
    enterprise_query_service: object | None = None,
    rule_analysis_service: object | None = None,
) -> None:
    register_repository_tools(server, queries)
    register_assessment_tools(server, queries)
    register_snapshot_tools(server, queries)
    register_finding_tools(server, queries)
    register_recommendation_tools(server, queries)
    register_component_tools(server, queries)
    register_artifact_tools(server, queries)
    register_execution_tools(
        server,
        queries=queries,
        assessment_service=assessment_service,
        settings=settings,
    )
    if agent_orchestrator is not None:
        register_agent_tools(
            server,
            orchestrator=agent_orchestrator,
            queries=queries,
            assessment_service=assessment_service,
            settings=settings,
        )
    register_incremental_tools(
        server,
        operations=incremental_operations,  # type: ignore[arg-type]
        inspection=incremental_inspection,  # type: ignore[arg-type]
    )
    register_enterprise_tools(
        server,
        knowledge_service=enterprise_knowledge_service,  # type: ignore[arg-type]
        query_service=enterprise_query_service,  # type: ignore[arg-type]
    )
    register_rules_tools(
        server,
        rule_analysis_service=rule_analysis_service,  # type: ignore[arg-type]
    )
