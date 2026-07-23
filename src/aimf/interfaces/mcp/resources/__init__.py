"""High-value MCP resources backed by KnowledgeQueryService."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.interfaces.mcp.errors import call_tool
from aimf.interfaces.mcp.mapping import to_mcp_payload
from aimf.interfaces.mcp.resources.enterprise import register_enterprise_resources


def register_resources(
    server: FastMCP,
    queries: KnowledgeQueryService,
    *,
    enterprise_query_service: EnterpriseKnowledgeQueryService | None = None,
) -> None:
    @server.resource("codestrata://repositories", mime_type="application/json")
    def repositories() -> str:
        """List registered repositories."""

        def _run() -> str:
            items = queries.list_repositories()
            return json.dumps(to_mcp_payload(items), indent=2, ensure_ascii=False)

        return call_tool("resource:repositories", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://repositories/{repository_id}",
        mime_type="application/json",
    )
    def repository(repository_id: str) -> str:
        """Get one repository summary."""

        def _run() -> str:
            item = queries.get_repository(repository_id)
            return json.dumps(to_mcp_payload(item), indent=2, ensure_ascii=False)

        return call_tool("resource:repository", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://repositories/{repository_id}/latest-assessment",
        mime_type="application/json",
    )
    def latest_assessment(repository_id: str) -> str:
        """Get latest completed assessment for a repository."""

        def _run() -> str:
            item = queries.get_latest_completed_run(repository_id)
            return json.dumps(to_mcp_payload(item), indent=2, ensure_ascii=False)

        return call_tool("resource:latest_assessment", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://assessments/{run_id}/findings",
        mime_type="application/json",
    )
    def findings(run_id: str) -> str:
        """List Phase 3 findings for an assessment."""

        def _run() -> str:
            items = queries.get_findings(run_id)
            return json.dumps(to_mcp_payload(items), indent=2, ensure_ascii=False)

        return call_tool("resource:findings", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://assessments/{run_id}/recommendations",
        mime_type="application/json",
    )
    def recommendations(run_id: str) -> str:
        """List Phase 3 recommendations for an assessment."""

        def _run() -> str:
            items = queries.get_recommendations(run_id)
            return json.dumps(to_mcp_payload(items), indent=2, ensure_ascii=False)

        return call_tool("resource:recommendations", _run)  # type: ignore[return-value]

    register_enterprise_resources(server, query_service=enterprise_query_service)
