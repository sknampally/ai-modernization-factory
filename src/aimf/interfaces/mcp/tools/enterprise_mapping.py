"""MCP DTO mapping for enterprise tools."""

from __future__ import annotations

from typing import Any

from aimf.application.enterprise.errors import EnterpriseApplicationError
from aimf.application.enterprise.models import (
    EnterpriseBuildResult,
    EnterpriseGraphDiff,
    EnterpriseImpactSummary,
    EnterpriseManifestValidationResult,
    EnterpriseNeighborhood,
)
from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph


def map_validation(result: EnterpriseManifestValidationResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def map_build(result: EnterpriseBuildResult) -> dict[str, Any]:
    return {
        "graph_id": result.graph.graph_id,
        "enterprise_id": result.graph.enterprise_id,
        "entity_count": len(result.graph.entities),
        "relationship_count": len(result.graph.relationships),
        "validation": map_validation(result.validation),
        "graph_fingerprint": result.graph.graph_fingerprint,
        "duration_ms": result.duration_ms,
    }


def map_graph(graph: EnterpriseKnowledgeGraph) -> dict[str, Any]:
    return {
        "graph_id": graph.graph_id,
        "enterprise_id": graph.enterprise_id,
        "schema_version": graph.schema_version,
        "entity_count": len(graph.entities),
        "relationship_count": len(graph.relationships),
        "repository_links": list(graph.repository_links),
        "graph_fingerprint": graph.graph_fingerprint,
    }


def map_neighborhood(value: EnterpriseNeighborhood) -> dict[str, Any]:
    return value.model_dump(mode="json")


def map_impact(value: EnterpriseImpactSummary) -> dict[str, Any]:
    return value.model_dump(mode="json")


def map_diff(value: EnterpriseGraphDiff) -> dict[str, Any]:
    return value.model_dump(mode="json")


def map_enterprise_error(error: BaseException) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": True,
        "message": str(error),
        "reason_code": getattr(error, "reason_code", "enterprise_error"),
    }
    if isinstance(error, EnterpriseApplicationError):
        if error.entity_id:
            payload["entity_id"] = error.entity_id
        if error.relationship_id:
            payload["relationship_id"] = error.relationship_id
        if error.manifest_path:
            payload["manifest_path"] = error.manifest_path
        if error.field_path:
            payload["field_path"] = error.field_path
    return payload
