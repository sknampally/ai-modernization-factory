"""MCP resources for Enterprise Knowledge Graph (read-only, bounded)."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from aimf.application.enterprise.errors import EnterpriseApplicationError
from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.interfaces.mcp.errors import call_tool
from aimf.interfaces.mcp.mapping import to_mcp_payload
from aimf.interfaces.mcp.tools.enterprise_mapping import map_graph, map_impact


def register_enterprise_resources(
    server: FastMCP,
    *,
    query_service: EnterpriseKnowledgeQueryService | None,
    default_enterprise_id: str = "enterprise:acme",
) -> None:
    if query_service is None:
        return

    @server.resource("codestrata://enterprise/graphs/latest", mime_type="application/json")
    def latest_graph() -> str:
        def _run() -> str:
            graph = query_service.get_latest_graph(default_enterprise_id)
            return json.dumps(map_graph(graph), indent=2, ensure_ascii=False)

        return call_tool("resource:enterprise_latest_graph", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://enterprise/graphs/{graph_id}",
        mime_type="application/json",
    )
    def graph_by_id(graph_id: str) -> str:
        def _run() -> str:
            graph = query_service.get_graph(graph_id)
            return json.dumps(map_graph(graph), indent=2, ensure_ascii=False)

        return call_tool("resource:enterprise_graph", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://enterprise/entities/{entity_id}",
        mime_type="application/json",
    )
    def entity(entity_id: str) -> str:
        def _run() -> str:
            view = query_service.get_entity(entity_id, enterprise_id=default_enterprise_id)
            return json.dumps(to_mcp_payload(view), indent=2, ensure_ascii=False)

        return call_tool("resource:enterprise_entity", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://enterprise/entities/{entity_id}/relationships",
        mime_type="application/json",
    )
    def entity_relationships(entity_id: str) -> str:
        def _run() -> str:
            neighborhood = query_service.get_neighborhood(
                entity_id,
                depth=1,
                enterprise_id=default_enterprise_id,
            )
            return json.dumps(to_mcp_payload(neighborhood), indent=2, ensure_ascii=False)

        return call_tool("resource:enterprise_entity_relationships", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://enterprise/repositories/{repository_id}/context",
        mime_type="application/json",
    )
    def repository_context(repository_id: str) -> str:
        def _run() -> str:
            entity_id = (
                repository_id
                if ":" in repository_id
                else f"repository:{repository_id}"
            )
            return json.dumps(
                map_impact(
                    query_service.repository_context(
                        entity_id,
                        enterprise_id=default_enterprise_id,
                    )
                ),
                indent=2,
                ensure_ascii=False,
            )

        return call_tool("resource:enterprise_repository_context", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://enterprise/findings/{finding_id}/impact",
        mime_type="application/json",
    )
    def finding_impact(finding_id: str) -> str:
        def _run() -> str:
            entity_id = finding_id if ":" in finding_id else f"finding:{finding_id}"
            return json.dumps(
                map_impact(
                    query_service.finding_impact(
                        entity_id,
                        enterprise_id=default_enterprise_id,
                    )
                ),
                indent=2,
                ensure_ascii=False,
            )

        return call_tool("resource:enterprise_finding_impact", _run)  # type: ignore[return-value]

    @server.resource(
        "codestrata://enterprise/recommendations/{recommendation_id}/impact",
        mime_type="application/json",
    )
    def recommendation_impact(recommendation_id: str) -> str:
        def _run() -> str:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            entity_id = (
                recommendation_id
                if ":" in recommendation_id
                else f"recommendation:{recommendation_id}"
            )
            return json.dumps(
                map_impact(
                    query_service.recommendation_impact(
                        entity_id,
                        enterprise_id=default_enterprise_id,
                    )
                ),
                indent=2,
                ensure_ascii=False,
            )

        return call_tool("resource:enterprise_recommendation_impact", _run)  # type: ignore[return-value]
