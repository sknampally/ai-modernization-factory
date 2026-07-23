"""FastMCP server construction for CodeStrata."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aimf.application.agents import AgentOrchestrator
from aimf.application.assessment import AssessmentApplicationService
from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.config import AimfSettings
from aimf.interfaces.mcp.prompts import register_prompts
from aimf.interfaces.mcp.resources import register_resources
from aimf.interfaces.mcp.tools import register_all_tools

CODESSTRATA_MCP_NAME = "CodeStrata"
CODESSTRATA_MCP_INSTRUCTIONS = (
    "CodeStrata modernization knowledge server. Query durable assessment "
    "knowledge and optionally run assessments. Prefer list/get/explain tools "
    "for precise queries; use *_with_agents tools for bounded multi-step "
    "workflows. Agents and other adapters should call application services "
    "directly rather than nesting through this MCP server."
)


def build_mcp_server(
    *,
    queries: KnowledgeQueryService,
    assessment_service: AssessmentApplicationService,
    settings: AimfSettings | None = None,
    agent_orchestrator: AgentOrchestrator | None = None,
    incremental_operations: object | None = None,
    incremental_inspection: object | None = None,
    enterprise_knowledge_service: object | None = None,
    enterprise_query_service: object | None = None,
    rule_analysis_service: object | None = None,
) -> FastMCP:
    """Assemble a FastMCP server with tools, resources, and prompts registered."""

    server = FastMCP(
        name=CODESSTRATA_MCP_NAME,
        instructions=CODESSTRATA_MCP_INSTRUCTIONS,
    )
    register_all_tools(
        server,
        queries=queries,
        assessment_service=assessment_service,
        settings=settings,
        agent_orchestrator=agent_orchestrator,
        incremental_operations=incremental_operations,
        incremental_inspection=incremental_inspection,
        enterprise_knowledge_service=enterprise_knowledge_service,
        enterprise_query_service=enterprise_query_service,
        rule_analysis_service=rule_analysis_service,
    )
    enterprise_queries = (
        enterprise_query_service
        if isinstance(enterprise_query_service, EnterpriseKnowledgeQueryService)
        else None
    )
    register_resources(
        server,
        queries,
        enterprise_query_service=enterprise_queries,
    )
    register_prompts(server, queries)
    return server
