"""Transport-neutral enterprise knowledge orchestration."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from aimf.application.enterprise.errors import (
    EnterpriseGraphValidationError,
    EnterpriseManifestValidationError,
    EnterpriseWorkspaceNotFoundError,
)
from aimf.application.enterprise.graph_builder import EnterpriseGraphBuilder
from aimf.application.enterprise.graph_comparator import EnterpriseGraphComparator
from aimf.application.enterprise.graph_linker import EnterpriseGraphLinker
from aimf.application.enterprise.models import (
    EnterpriseBuildResult,
    EnterpriseGraphDiff,
    EnterpriseManifestValidationResult,
    EnterprisePolicy,
    EnterpriseWorkspaceInitResult,
)
from aimf.application.enterprise.ports import (
    EnterpriseGraphRepository,
    EnterpriseManifestSnapshotRepository,
    EnterpriseManifestSource,
    RepositoryIdentityResolver,
)
from aimf.application.enterprise.validation_service import (
    EnterpriseManifestValidationService,
)
from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph

logger = logging.getLogger(__name__)


class EnterpriseKnowledgeService:
    def __init__(
        self,
        *,
        manifest_source: EnterpriseManifestSource,
        graph_repository: EnterpriseGraphRepository | None = None,
        snapshot_repository: EnterpriseManifestSnapshotRepository | None = None,
        resolver: RepositoryIdentityResolver | None = None,
        policy: EnterprisePolicy | None = None,
        validator: EnterpriseManifestValidationService | None = None,
        builder: EnterpriseGraphBuilder | None = None,
        linker: EnterpriseGraphLinker | None = None,
    ) -> None:
        self._source = manifest_source
        self._graphs = graph_repository
        self._snapshots = snapshot_repository
        self._resolver = resolver
        self._policy = policy or EnterprisePolicy()
        self._validator = validator or EnterpriseManifestValidationService()
        self._builder = builder or EnterpriseGraphBuilder()
        self._linker = linker or EnterpriseGraphLinker()
        self._comparator = EnterpriseGraphComparator()

    def validate_workspace(self, workspace: str) -> EnterpriseManifestValidationResult:
        collection = self._source.load(workspace)
        return self._validator.validate(collection, policy=self._policy, resolver=self._resolver)

    def build_graph(
        self,
        workspace: str,
        *,
        link_assessments: bool | None = None,
    ) -> EnterpriseBuildResult:
        started = time.perf_counter()
        collection = self._source.load(workspace)
        validation = self._validator.validate(
            collection, policy=self._policy, resolver=self._resolver
        )
        if validation.status != "passed":
            raise EnterpriseManifestValidationError(
                "Enterprise workspace validation failed",
                reason_code="validation_failed",
            )
        graph = self._builder.build(collection, policy=self._policy, resolver=self._resolver)
        linked_repos = len(graph.repository_links)
        linked_assessments = 0
        do_link = (
            self._policy.link_repository_assessments
            if link_assessments is None
            else link_assessments
        )
        if do_link:
            # Assessment linking is explicit via link_latest_assessments; build stays complete.
            pass

        if self._policy.persist_graph and self._graphs is not None:
            self._graphs.save_graph(graph)
            if self._policy.persist_manifest_snapshot and self._snapshots is not None:
                self._snapshots.save_manifest_snapshot(
                    enterprise_id=graph.enterprise_id,
                    graph_id=graph.graph_id,
                    collection=collection,
                )

        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "enterprise.graph_built",
            extra={
                "enterprise_id": graph.enterprise_id,
                "graph_id": graph.graph_id,
                "entity_count": len(graph.entities),
                "relationship_count": len(graph.relationships),
                "unresolved_repository_count": len(validation.unresolved_repository_references),
                "duration_ms": duration_ms,
            },
        )
        return EnterpriseBuildResult(
            graph=graph,
            validation=validation,
            linked_repository_count=linked_repos,
            linked_assessment_count=linked_assessments,
            duration_ms=duration_ms,
        )

    def link_latest_assessments(
        self,
        graph: EnterpriseKnowledgeGraph,
        *,
        codestrata_repository_id: str,
        snapshot_id: str | None = None,
        run_id: str | None = None,
        finding_ids: tuple[str, ...] = (),
        recommendation_ids: tuple[str, ...] = (),
        persist: bool = True,
    ) -> EnterpriseKnowledgeGraph:
        linked = self._linker.link_assessment(
            graph,
            codestrata_repository_id=codestrata_repository_id,
            snapshot_id=snapshot_id,
            run_id=run_id,
            finding_ids=finding_ids,
            recommendation_ids=recommendation_ids,
        )
        if not linked.entities or not linked.graph_fingerprint:
            raise EnterpriseGraphValidationError(
                "Linked graph is incomplete",
                reason_code="incomplete_linked_graph",
            )
        if persist and self._graphs is not None:
            # Persist as a new version (immutable prior versions).
            from uuid import uuid4

            versioned = linked.model_copy(update={"graph_id": str(uuid4())})
            self._graphs.save_graph(versioned)
            return versioned
        return linked

    def get_graph(self, graph_id: str) -> EnterpriseKnowledgeGraph:
        if self._graphs is None:
            raise EnterpriseGraphValidationError(
                "Graph repository is not configured",
                reason_code="graph_repository_missing",
            )
        return self._graphs.get_graph(graph_id)

    def get_latest_graph(self, enterprise_id: str) -> EnterpriseKnowledgeGraph:
        if self._graphs is None:
            raise EnterpriseGraphValidationError(
                "Graph repository is not configured",
                reason_code="graph_repository_missing",
            )
        return self._graphs.get_latest_graph(enterprise_id)

    def compare_graph_versions(
        self, left_graph_id: str, right_graph_id: str
    ) -> EnterpriseGraphDiff:
        if self._graphs is None:
            raise EnterpriseGraphValidationError(
                "Graph repository is not configured",
                reason_code="graph_repository_missing",
            )
        left = self._graphs.get_graph(left_graph_id)
        right = self._graphs.get_graph(right_graph_id)
        return self._comparator.compare(left, right)

    def init_workspace(
        self,
        workspace: str,
        *,
        examples: bool = False,
        force: bool = False,
        writer: object | None = None,
    ) -> EnterpriseWorkspaceInitResult:
        if writer is None:
            raise EnterpriseWorkspaceNotFoundError(
                "Workspace writer is required for init",
                reason_code="writer_missing",
            )
        created = writer.create_workspace(  # type: ignore[attr-defined]
            workspace, examples=examples, force=force
        )
        return EnterpriseWorkspaceInitResult(
            workspace=workspace,
            files_created=tuple(created),
            validated=True,
            created_at=datetime.now(UTC),
        )
