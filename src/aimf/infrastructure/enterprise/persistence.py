"""File-backed enterprise graph persistence (no graph database)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from aimf.application.enterprise.errors import (
    EnterpriseGraphNotFoundError,
    EnterpriseGraphPersistenceError,
)
from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph
from aimf.domain.enterprise.manifests import EnterpriseManifestCollection

logger = logging.getLogger(__name__)


class FileEnterpriseGraphRepository:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save_graph(self, graph: EnterpriseKnowledgeGraph) -> None:
        path = self._root / f"{graph.graph_id}.json"
        try:
            path.write_text(
                json.dumps(graph.model_dump(mode="json"), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            latest = self._root / f"latest-{_safe(graph.enterprise_id)}.json"
            latest.write_text(
                json.dumps({"graph_id": graph.graph_id}, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as error:
            raise EnterpriseGraphPersistenceError(
                "Failed to persist enterprise graph",
                reason_code="graph_persist_failed",
            ) from error
        logger.info(
            "enterprise.graph_saved",
            extra={
                "graph_id": graph.graph_id,
                "enterprise_id": graph.enterprise_id,
                "entity_count": len(graph.entities),
                "relationship_count": len(graph.relationships),
            },
        )

    def get_graph(self, graph_id: str) -> EnterpriseKnowledgeGraph:
        path = self._root / f"{_safe(graph_id)}.json"
        if not path.is_file():
            raise EnterpriseGraphNotFoundError(
                "Enterprise graph not found",
                reason_code="graph_not_found",
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        return EnterpriseKnowledgeGraph.model_validate(payload)

    def get_latest_graph(self, enterprise_id: str) -> EnterpriseKnowledgeGraph:
        latest = self._root / f"latest-{_safe(enterprise_id)}.json"
        if not latest.is_file():
            raise EnterpriseGraphNotFoundError(
                "Latest enterprise graph not found",
                reason_code="latest_graph_not_found",
            )
        pointer = json.loads(latest.read_text(encoding="utf-8"))
        return self.get_graph(str(pointer["graph_id"]))

    def list_graph_versions(
        self,
        enterprise_id: str,
        *,
        limit: int = 50,
    ) -> tuple[EnterpriseKnowledgeGraph, ...]:
        graphs: list[EnterpriseKnowledgeGraph] = []
        for path in sorted(self._root.glob("*.json")):
            if path.name.startswith("latest-"):
                continue
            try:
                graph = EnterpriseKnowledgeGraph.model_validate(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except (OSError, ValueError, TypeError):
                continue
            if graph.enterprise_id == enterprise_id:
                graphs.append(graph)
        graphs.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(graphs[: max(1, limit)])


class FileEnterpriseManifestSnapshotRepository:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save_manifest_snapshot(
        self,
        *,
        enterprise_id: str,
        graph_id: str,
        collection: EnterpriseManifestCollection,
    ) -> None:
        path = self._root / f"{_safe(graph_id)}.json"
        path.write_text(
            json.dumps(collection.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def get_manifest_snapshot(self, graph_id: str) -> EnterpriseManifestCollection:
        path = self._root / f"{_safe(graph_id)}.json"
        if not path.is_file():
            raise EnterpriseGraphNotFoundError(
                "Manifest snapshot not found",
                reason_code="manifest_snapshot_not_found",
            )
        return EnterpriseManifestCollection.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )


def _safe(value: str) -> str:
    return value.strip().replace("/", "_").replace("..", "_").replace(":", "_")
