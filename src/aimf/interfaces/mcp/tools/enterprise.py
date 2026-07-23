"""Additive MCP tools for Enterprise Knowledge Graph."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from aimf.application.enterprise.errors import EnterpriseApplicationError
from aimf.application.enterprise.knowledge_service import EnterpriseKnowledgeService
from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.domain.enterprise.enums import EnterpriseEntityKind
from aimf.interfaces.mcp.tools._common import require_nonblank, run_bounded
from aimf.interfaces.mcp.tools.enterprise_mapping import (
    map_build,
    map_diff,
    map_graph,
    map_impact,
    map_neighborhood,
    map_validation,
)


def register_enterprise_tools(
    server: FastMCP,
    *,
    knowledge_service: EnterpriseKnowledgeService | None,
    query_service: EnterpriseKnowledgeQueryService | None,
) -> None:
    @server.tool(name="validate_enterprise_workspace", structured_output=True)
    def validate_enterprise_workspace(workspace: str = "enterprise") -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if knowledge_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise knowledge service is not configured",
                    reason_code="enterprise_service_missing",
                )
            result = knowledge_service.validate_workspace(
                require_nonblank(workspace, label="workspace")
            )
            return map_validation(result)

        return run_bounded("validate_enterprise_workspace", _run)

    @server.tool(name="build_enterprise_knowledge_graph", structured_output=True)
    def build_enterprise_knowledge_graph(
        workspace: str = "enterprise",
        link_assessments: bool = False,
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if knowledge_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise knowledge service is not configured",
                    reason_code="enterprise_service_missing",
                )
            result = knowledge_service.build_graph(
                require_nonblank(workspace, label="workspace"),
                link_assessments=link_assessments,
            )
            return map_build(result)

        return run_bounded("build_enterprise_knowledge_graph", _run)

    @server.tool(name="get_enterprise_graph", structured_output=True)
    def get_enterprise_graph(
        enterprise_id: str = "enterprise:acme",
        graph_id: str | None = None,
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            graph = (
                query_service.get_graph(require_nonblank(graph_id, label="graph_id"))
                if graph_id
                else query_service.get_latest_graph(
                    require_nonblank(enterprise_id, label="enterprise_id")
                )
            )
            return map_graph(graph)

        return run_bounded("get_enterprise_graph", _run)

    @server.tool(name="get_enterprise_entity", structured_output=True)
    def get_enterprise_entity(
        entity_id: str,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            entity = query_service.get_entity(
                require_nonblank(entity_id, label="entity_id"),
                enterprise_id=enterprise_id,
            )
            return entity.model_dump(mode="json")

        return run_bounded("get_enterprise_entity", _run)

    @server.tool(name="query_enterprise_entities", structured_output=True)
    def query_enterprise_entities(
        kind: str,
        enterprise_id: str = "enterprise:acme",
        limit: int = 100,
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            items = query_service.list_entities(
                kind=EnterpriseEntityKind(require_nonblank(kind, label="kind")),
                enterprise_id=enterprise_id,
                limit=limit,
            )
            return {"entities": [item.model_dump(mode="json") for item in items]}

        return run_bounded("query_enterprise_entities", _run)

    @server.tool(name="get_enterprise_entity_neighborhood", structured_output=True)
    def get_enterprise_entity_neighborhood(
        entity_id: str,
        depth: int = 1,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            return map_neighborhood(
                query_service.get_neighborhood(
                    require_nonblank(entity_id, label="entity_id"),
                    depth=depth,
                    enterprise_id=enterprise_id,
                )
            )

        return run_bounded("get_enterprise_entity_neighborhood", _run)

    @server.tool(name="trace_enterprise_dependency_path", structured_output=True)
    def trace_enterprise_dependency_path(
        source_entity_id: str,
        target_entity_id: str,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            paths = query_service.trace_dependency_paths(
                require_nonblank(source_entity_id, label="source_entity_id"),
                require_nonblank(target_entity_id, label="target_entity_id"),
                enterprise_id=enterprise_id,
            )
            return {"paths": [list(path) for path in paths]}

        return run_bounded("trace_enterprise_dependency_path", _run)

    @server.tool(name="get_repository_enterprise_context", structured_output=True)
    def get_repository_enterprise_context(
        repository_entity_id: str,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            return map_impact(
                query_service.repository_context(
                    require_nonblank(repository_entity_id, label="repository_entity_id"),
                    enterprise_id=enterprise_id,
                )
            )

        return run_bounded("get_repository_enterprise_context", _run)

    @server.tool(name="get_finding_enterprise_impact", structured_output=True)
    def get_finding_enterprise_impact(
        finding_entity_id: str,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            return map_impact(
                query_service.finding_impact(
                    require_nonblank(finding_entity_id, label="finding_entity_id"),
                    enterprise_id=enterprise_id,
                )
            )

        return run_bounded("get_finding_enterprise_impact", _run)

    @server.tool(name="get_recommendation_enterprise_impact", structured_output=True)
    def get_recommendation_enterprise_impact(
        recommendation_entity_id: str,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            return map_impact(
                query_service.recommendation_impact(
                    require_nonblank(recommendation_entity_id, label="recommendation_entity_id"),
                    enterprise_id=enterprise_id,
                )
            )

        return run_bounded("get_recommendation_enterprise_impact", _run)

    @server.tool(name="explain_enterprise_relationship", structured_output=True)
    def explain_enterprise_relationship(
        relationship_id: str,
        enterprise_id: str = "enterprise:acme",
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if query_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise query service is not configured",
                    reason_code="enterprise_query_missing",
                )
            graph = query_service.get_latest_graph(enterprise_id)
            match = next(
                (
                    rel
                    for rel in graph.relationships
                    if str(rel.relationship_id)
                    == require_nonblank(relationship_id, label="relationship_id")
                ),
                None,
            )
            if match is None:
                raise EnterpriseApplicationError(
                    "Relationship not found",
                    reason_code="entity_not_found",
                    relationship_id=relationship_id,
                )
            return {
                "relationship_id": str(match.relationship_id),
                "kind": match.kind.value,
                "source": str(match.source_entity_id),
                "target": str(match.target_entity_id),
                "provenance_category": match.provenance.category.value,
                "derivation_rule": match.provenance.derivation_rule,
                "confidence": match.provenance.confidence,
                "source_ref": match.provenance.source_ref,
            }

        return run_bounded("explain_enterprise_relationship", _run)

    @server.tool(name="compare_enterprise_graph_versions", structured_output=True)
    def compare_enterprise_graph_versions(
        left_graph_id: str,
        right_graph_id: str,
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if knowledge_service is None:
                raise EnterpriseApplicationError(
                    "Enterprise knowledge service is not configured",
                    reason_code="enterprise_service_missing",
                )
            return map_diff(
                knowledge_service.compare_graph_versions(
                    require_nonblank(left_graph_id, label="left_graph_id"),
                    require_nonblank(right_graph_id, label="right_graph_id"),
                )
            )

        return run_bounded("compare_enterprise_graph_versions", _run)
