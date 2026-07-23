"""CLI mapping for enterprise commands."""

from __future__ import annotations

import json
from typing import Any

from aimf.application.enterprise.errors import EnterpriseApplicationError
from aimf.application.enterprise.models import (
    EnterpriseBuildResult,
    EnterpriseGraphDiff,
    EnterpriseManifestValidationResult,
)
from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph

EXIT_SUCCESS = 0
EXIT_BLOCKED = 1
EXIT_ERROR = 2


def dumps_json(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def validation_to_dict(result: EnterpriseManifestValidationResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def build_to_dict(result: EnterpriseBuildResult) -> dict[str, Any]:
    return {
        "graph_id": result.graph.graph_id,
        "enterprise_id": result.graph.enterprise_id,
        "entity_count": len(result.graph.entities),
        "relationship_count": len(result.graph.relationships),
        "linked_repository_count": result.linked_repository_count,
        "validation": validation_to_dict(result.validation),
        "duration_ms": result.duration_ms,
        "graph_fingerprint": result.graph.graph_fingerprint,
    }


def graph_summary_to_dict(graph: EnterpriseKnowledgeGraph) -> dict[str, Any]:
    return {
        "graph_id": graph.graph_id,
        "enterprise_id": graph.enterprise_id,
        "schema_version": graph.schema_version,
        "entity_count": len(graph.entities),
        "relationship_count": len(graph.relationships),
        "repository_links": list(graph.repository_links),
        "graph_fingerprint": graph.graph_fingerprint,
        "source_fingerprint": graph.source_fingerprint,
    }


def diff_to_dict(diff: EnterpriseGraphDiff) -> dict[str, Any]:
    return diff.model_dump(mode="json")


def exit_code_for_error(error: BaseException) -> int:
    if isinstance(error, EnterpriseApplicationError):
        if error.reason_code in {
            "validation_failed",
            "entity_not_found",
            "graph_not_found",
            "latest_graph_not_found",
        }:
            return EXIT_BLOCKED
        return EXIT_ERROR
    return EXIT_ERROR
