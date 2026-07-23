"""Enterprise knowledge query service (bounded, cycle-safe)."""

from __future__ import annotations

from aimf.application.enterprise.errors import (
    EnterpriseEntityNotFoundError,
    EnterpriseGraphNotFoundError,
    EnterpriseQueryLimitError,
    EnterpriseTraversalLimitError,
)
from aimf.application.enterprise.models import (
    EnterpriseEntityView,
    EnterpriseImpactSummary,
    EnterpriseNeighborhood,
    EnterprisePolicy,
    EnterpriseRelationshipView,
)
from aimf.application.enterprise.ports import EnterpriseGraphRepository
from aimf.domain.enterprise.entities import EnterpriseEntity, EnterpriseKnowledgeGraph
from aimf.domain.enterprise.enums import (
    EnterpriseEntityKind,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
)


class EnterpriseKnowledgeQueryService:
    def __init__(
        self,
        repository: EnterpriseGraphRepository,
        *,
        policy: EnterprisePolicy | None = None,
    ) -> None:
        self._repo = repository
        self._policy = policy or EnterprisePolicy()

    def get_latest_graph(self, enterprise_id: str) -> EnterpriseKnowledgeGraph:
        return self._repo.get_latest_graph(enterprise_id)

    def get_graph(self, graph_id: str) -> EnterpriseKnowledgeGraph:
        return self._repo.get_graph(graph_id)

    def get_entity(
        self,
        entity_id: str,
        *,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseEntityView:
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        entity = self._find_entity(graph, entity_id)
        return _view(entity)

    def list_entities(
        self,
        *,
        kind: EnterpriseEntityKind | None = None,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
        limit: int | None = None,
    ) -> tuple[EnterpriseEntityView, ...]:
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        bound = min(limit or self._policy.max_query_results, self._policy.max_query_results)
        items = [_view(entity) for entity in graph.entities if kind is None or entity.kind is kind]
        items.sort(key=lambda item: item.entity_id)
        if len(items) > bound:
            raise EnterpriseQueryLimitError(
                f"Query exceeded max_query_results ({bound})",
                reason_code="query_limit",
            )
        return tuple(items[:bound])

    def list_by_relationship(
        self,
        *,
        source_id: str | None = None,
        target_id: str | None = None,
        kind: EnterpriseRelationshipKind | None = None,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
        limit: int | None = None,
    ) -> tuple[EnterpriseEntityView, ...]:
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        bound = min(limit or self._policy.max_query_results, self._policy.max_query_results)
        entity_map = {str(item.entity_id): item for item in graph.entities}
        selected: list[EnterpriseEntity] = []
        for rel in graph.relationships:
            if kind is not None and rel.kind is not kind:
                continue
            if source_id is not None and rel.source_entity_id.root != source_id:
                continue
            if target_id is not None and rel.target_entity_id.root != target_id:
                continue
            neighbor_id = (
                rel.target_entity_id.root if source_id is not None else rel.source_entity_id.root
            )
            if neighbor_id in entity_map:
                selected.append(entity_map[neighbor_id])
        unique = {str(item.entity_id): item for item in selected}
        views = sorted(
            (_view(item) for item in unique.values()),
            key=lambda item: item.entity_id,
        )
        return tuple(views[:bound])

    def get_neighborhood(
        self,
        entity_id: str,
        *,
        depth: int = 1,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseNeighborhood:
        if depth < 1 or depth > self._policy.max_traversal_depth:
            raise EnterpriseTraversalLimitError(
                f"depth must be between 1 and {self._policy.max_traversal_depth}",
                reason_code="traversal_depth_limit",
            )
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        entity = self._find_entity(graph, entity_id)
        entity_map = {str(item.entity_id): item for item in graph.entities}
        frontier = {entity_id}
        seen = {entity_id}
        rels: list[EnterpriseRelationshipView] = []
        neighbors: list[EnterpriseEntityView] = []
        truncated = False
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in sorted(frontier):
                for rel in graph.relationships:
                    other: str | None = None
                    if rel.source_entity_id.root == node:
                        other = rel.target_entity_id.root
                    elif rel.target_entity_id.root == node:
                        other = rel.source_entity_id.root
                    if other is None:
                        continue
                    rels.append(_rel_view(rel))
                    if other in seen:
                        continue
                    seen.add(other)
                    next_frontier.add(other)
                    if other in entity_map:
                        neighbors.append(_view(entity_map[other]))
                    if len(neighbors) >= self._policy.max_query_results:
                        truncated = True
                        break
                if truncated:
                    break
            frontier = next_frontier
            if truncated or not frontier:
                break
        return EnterpriseNeighborhood(
            entity=_view(entity),
            relationships=tuple(sorted(rels, key=lambda item: item.relationship_id))[
                : self._policy.max_query_results
            ],
            neighbors=tuple(sorted(neighbors, key=lambda item: item.entity_id)),
            truncated=truncated,
            depth=depth,
        )

    def trace_dependency_paths(
        self,
        source_id: str,
        target_id: str,
        *,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> tuple[tuple[str, ...], ...]:
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        adjacency: dict[str, list[str]] = {}
        for rel in graph.relationships:
            adjacency.setdefault(rel.source_entity_id.root, []).append(rel.target_entity_id.root)
        paths: list[tuple[str, ...]] = []
        stack: list[tuple[str, ...]] = [(source_id,)]

        while stack and len(paths) < self._policy.max_dependency_paths:
            path = stack.pop()
            if len(path) > self._policy.max_traversal_depth + 1:
                continue
            current = path[-1]
            if current == target_id and len(path) > 1:
                paths.append(path)
                continue
            for nxt in sorted(adjacency.get(current, [])):
                if nxt in path:
                    continue
                stack.append(path + (nxt,))
        return tuple(sorted(paths))

    def repository_context(
        self,
        repository_entity_id: str,
        *,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseImpactSummary:
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        apps = self.list_by_relationship(
            target_id=repository_entity_id,
            kind=EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
            graph_id=graph.graph_id,
        )
        services = self.list_by_relationship(
            target_id=repository_entity_id,
            kind=EnterpriseRelationshipKind.SERVICE_IMPLEMENTED_BY_REPOSITORY,
            graph_id=graph.graph_id,
        )
        capabilities: list[EnterpriseEntityView] = []
        for app in apps:
            capabilities.extend(
                self.list_by_relationship(
                    source_id=app.entity_id,
                    kind=EnterpriseRelationshipKind.APPLICATION_SUPPORTS_CAPABILITY,
                    graph_id=graph.graph_id,
                )
            )
        impacted = tuple(
            sorted(
                {item.entity_id: item for item in (*apps, *services, *capabilities)}.values(),
                key=lambda item: item.entity_id,
            )
        )
        return EnterpriseImpactSummary(
            source_entity_id=repository_entity_id,
            impacted_entities=impacted,
            paths=tuple((repository_entity_id, item.entity_id) for item in impacted),
            declared_count=len(impacted),
            derived_count=0,
            limitations=(),
        )

    def finding_impact(
        self,
        finding_entity_id: str,
        *,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseImpactSummary:
        return self._assessment_artifact_impact(
            finding_entity_id,
            kinds=(
                EnterpriseRelationshipKind.FINDING_AFFECTS_APPLICATION,
                EnterpriseRelationshipKind.FINDING_AFFECTS_SERVICE,
                EnterpriseRelationshipKind.FINDING_AFFECTS_CAPABILITY,
            ),
            derived_categories=(
                EnterpriseProvenanceCategory.DERIVED_FINDING,
                EnterpriseProvenanceCategory.DERIVED_ASSESSMENT_GRAPH,
            ),
            graph_id=graph_id,
            enterprise_id=enterprise_id,
        )

    def recommendation_impact(
        self,
        recommendation_entity_id: str,
        *,
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseImpactSummary:
        return self._assessment_artifact_impact(
            recommendation_entity_id,
            kinds=(
                EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_APPLICATION,
                EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_SERVICE,
                EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_CAPABILITY,
            ),
            derived_categories=(
                EnterpriseProvenanceCategory.DERIVED_RECOMMENDATION,
                EnterpriseProvenanceCategory.DERIVED_ASSESSMENT_GRAPH,
            ),
            graph_id=graph_id,
            enterprise_id=enterprise_id,
        )

    def _assessment_artifact_impact(
        self,
        source_entity_id: str,
        *,
        kinds: tuple[EnterpriseRelationshipKind, ...],
        derived_categories: tuple[EnterpriseProvenanceCategory, ...],
        graph_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseImpactSummary:
        graph = self._resolve_graph(graph_id=graph_id, enterprise_id=enterprise_id)
        impacted: list[EnterpriseEntityView] = []
        for kind in kinds:
            impacted.extend(
                self.list_by_relationship(
                    source_id=source_entity_id,
                    kind=kind,
                    graph_id=graph.graph_id,
                )
            )
        views = tuple(
            sorted(
                {item.entity_id: item for item in impacted}.values(),
                key=lambda item: item.entity_id,
            )
        )
        derived = sum(
            1
            for rel in graph.relationships
            if rel.source_entity_id.root == source_entity_id
            and rel.provenance.category in derived_categories
        )
        return EnterpriseImpactSummary(
            source_entity_id=source_entity_id,
            impacted_entities=views,
            paths=tuple((source_entity_id, item.entity_id) for item in views),
            declared_count=0,
            derived_count=derived,
            limitations=("Impact requires declared repository→service/application paths",),
        )

    def _resolve_graph(
        self,
        *,
        graph_id: str | None,
        enterprise_id: str | None,
    ) -> EnterpriseKnowledgeGraph:
        if graph_id:
            return self._repo.get_graph(graph_id)
        if enterprise_id:
            return self._repo.get_latest_graph(enterprise_id)
        raise EnterpriseGraphNotFoundError(
            "graph_id or enterprise_id is required",
            reason_code="missing_graph_selector",
        )

    def _find_entity(self, graph: EnterpriseKnowledgeGraph, entity_id: str) -> EnterpriseEntity:
        for entity in graph.entities:
            if str(entity.entity_id) == entity_id:
                return entity
        raise EnterpriseEntityNotFoundError(
            f"Entity not found: {entity_id}",
            reason_code="entity_not_found",
            entity_id=entity_id,
        )


def _view(entity: EnterpriseEntity) -> EnterpriseEntityView:
    return EnterpriseEntityView(
        entity_id=str(entity.entity_id),
        kind=entity.kind,
        name=entity.name,
        description=entity.description,
        labels=dict(entity.labels),
        attributes=dict(entity.attributes),
        provenance_category=entity.provenance.category.value,
        lifecycle=entity.lifecycle.value,
        criticality=entity.criticality.value,
    )


def _rel_view(rel: object) -> EnterpriseRelationshipView:
    return EnterpriseRelationshipView(
        relationship_id=str(rel.relationship_id),  # type: ignore[attr-defined]
        kind=rel.kind,  # type: ignore[attr-defined]
        source_entity_id=str(rel.source_entity_id),  # type: ignore[attr-defined]
        target_entity_id=str(rel.target_entity_id),  # type: ignore[attr-defined]
        provenance_category=rel.provenance.category.value,  # type: ignore[attr-defined]
        metadata=dict(rel.metadata),  # type: ignore[attr-defined]
    )
