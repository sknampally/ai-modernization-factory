"""Application ports for enterprise knowledge."""

from __future__ import annotations

from typing import Protocol

from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph
from aimf.domain.enterprise.manifests import EnterpriseManifestCollection


class EnterpriseWorkspaceReference(Protocol):
    @property
    def relative_root(self) -> str: ...


class EnterpriseManifestSource(Protocol):
    def load(self, workspace_root: str) -> EnterpriseManifestCollection: ...


class EnterpriseGraphRepository(Protocol):
    def save_graph(self, graph: EnterpriseKnowledgeGraph) -> None: ...

    def get_graph(self, graph_id: str) -> EnterpriseKnowledgeGraph: ...

    def get_latest_graph(self, enterprise_id: str) -> EnterpriseKnowledgeGraph: ...

    def list_graph_versions(
        self,
        enterprise_id: str,
        *,
        limit: int = 50,
    ) -> tuple[EnterpriseKnowledgeGraph, ...]: ...


class EnterpriseManifestSnapshotRepository(Protocol):
    def save_manifest_snapshot(
        self,
        *,
        enterprise_id: str,
        graph_id: str,
        collection: EnterpriseManifestCollection,
    ) -> None: ...

    def get_manifest_snapshot(self, graph_id: str) -> EnterpriseManifestCollection: ...


class RepositoryIdentityResolver(Protocol):
    """Resolve enterprise repository references to CodeStrata registry IDs."""

    def resolve(self, reference: str) -> str | None:
        """Return canonical repository_id or None if unresolved."""
