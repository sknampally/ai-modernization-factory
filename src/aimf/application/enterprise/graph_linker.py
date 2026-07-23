"""Link enterprise graph to CodeStrata assessment knowledge (derived edges)."""

from __future__ import annotations

from datetime import UTC, datetime

from aimf.domain.enterprise.entities import (
    EnterpriseEntity,
    EnterpriseKnowledgeGraph,
    EnterpriseProvenance,
    EnterpriseRelationship,
)
from aimf.domain.enterprise.enums import (
    EnterpriseEntityKind,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
)
from aimf.domain.enterprise.identifiers import (
    EnterpriseEntityId,
    EnterpriseRelationshipId,
    build_entity_id,
    build_relationship_id,
)


class EnterpriseGraphLinker:
    """Attach assessment/finding/recommendation derived links when paths are clear."""

    def link_assessment(
        self,
        graph: EnterpriseKnowledgeGraph,
        *,
        codestrata_repository_id: str,
        snapshot_id: str | None = None,
        run_id: str | None = None,
        finding_ids: tuple[str, ...] = (),
        recommendation_ids: tuple[str, ...] = (),
    ) -> EnterpriseKnowledgeGraph:
        entities = {str(item.entity_id): item for item in graph.entities}
        relationships = {str(item.relationship_id): item for item in graph.relationships}
        now = datetime.now(UTC)
        derived = EnterpriseProvenance(
            category=EnterpriseProvenanceCategory.DERIVED_ASSESSMENT_GRAPH,
            derivation_rule="link_assessment",
            confidence="exact",
            recorded_at=now,
        )
        cs_repo = build_entity_id(
            EnterpriseEntityKind.CODESTRATA_REPOSITORY, codestrata_repository_id
        )
        if cs_repo not in entities:
            entities[cs_repo] = EnterpriseEntity(
                entity_id=EnterpriseEntityId(cs_repo),
                kind=EnterpriseEntityKind.CODESTRATA_REPOSITORY,
                name=codestrata_repository_id,
                provenance=derived,
            )

        if snapshot_id:
            snap = build_entity_id(EnterpriseEntityKind.CODESTRATA_SNAPSHOT, snapshot_id)
            entities[snap] = EnterpriseEntity(
                entity_id=EnterpriseEntityId(snap),
                kind=EnterpriseEntityKind.CODESTRATA_SNAPSHOT,
                name=snapshot_id,
                provenance=derived,
            )
            self._add(
                relationships,
                EnterpriseRelationshipKind.REPOSITORY_HAS_SNAPSHOT,
                cs_repo,
                snap,
                derived,
            )
            if run_id:
                run = build_entity_id(EnterpriseEntityKind.CODESTRATA_ASSESSMENT_RUN, run_id)
                entities[run] = EnterpriseEntity(
                    entity_id=EnterpriseEntityId(run),
                    kind=EnterpriseEntityKind.CODESTRATA_ASSESSMENT_RUN,
                    name=run_id,
                    provenance=derived,
                )
                self._add(
                    relationships,
                    EnterpriseRelationshipKind.SNAPSHOT_HAS_ASSESSMENT,
                    snap,
                    run,
                    derived,
                )
                for finding_id in finding_ids:
                    fid = build_entity_id(EnterpriseEntityKind.CODESTRATA_FINDING, finding_id)
                    entities[fid] = EnterpriseEntity(
                        entity_id=EnterpriseEntityId(fid),
                        kind=EnterpriseEntityKind.CODESTRATA_FINDING,
                        name=finding_id,
                        provenance=EnterpriseProvenance(
                            category=EnterpriseProvenanceCategory.DERIVED_FINDING,
                            derivation_rule="link_assessment",
                            recorded_at=now,
                        ),
                    )
                    self._add(
                        relationships,
                        EnterpriseRelationshipKind.ASSESSMENT_PRODUCED_FINDING,
                        run,
                        fid,
                        derived,
                    )
                    self._propagate_finding_impact(entities, relationships, cs_repo, fid, now)
                for recommendation_id in recommendation_ids:
                    rid = build_entity_id(
                        EnterpriseEntityKind.CODESTRATA_RECOMMENDATION,
                        recommendation_id,
                    )
                    entities[rid] = EnterpriseEntity(
                        entity_id=EnterpriseEntityId(rid),
                        kind=EnterpriseEntityKind.CODESTRATA_RECOMMENDATION,
                        name=recommendation_id,
                        provenance=EnterpriseProvenance(
                            category=EnterpriseProvenanceCategory.DERIVED_RECOMMENDATION,
                            derivation_rule="link_assessment",
                            recorded_at=now,
                        ),
                    )
                    self._add(
                        relationships,
                        EnterpriseRelationshipKind.ASSESSMENT_PRODUCED_RECOMMENDATION,
                        run,
                        rid,
                        derived,
                    )
                    self._propagate_recommendation_impact(
                        entities, relationships, cs_repo, rid, now
                    )

        return graph.model_copy(
            update={
                "entities": tuple(sorted(entities.values(), key=lambda item: str(item.entity_id))),
                "relationships": tuple(
                    sorted(
                        relationships.values(),
                        key=lambda item: str(item.relationship_id),
                    )
                ),
            }
        )

    def _propagate_finding_impact(
        self,
        entities: dict[str, EnterpriseEntity],
        relationships: dict[str, EnterpriseRelationship],
        cs_repo: str,
        finding_id: str,
        now: datetime,
    ) -> None:
        """Derive finding→service/application/capability only via declared paths."""

        derived = EnterpriseProvenance(
            category=EnterpriseProvenanceCategory.DERIVED_FINDING,
            derivation_rule="repository_to_service_application_capability",
            confidence="high",
            recorded_at=now,
        )
        # Enterprise repos that resolve to this CodeStrata repository.
        enterprise_repos = [
            rel.source_entity_id.root
            for rel in relationships.values()
            if rel.kind is EnterpriseRelationshipKind.REPOSITORY_RESOLVES_TO_CODESTRATA_REPOSITORY
            and rel.target_entity_id.root == cs_repo
        ]
        for ent_repo in enterprise_repos:
            services = [
                rel.source_entity_id.root
                for rel in relationships.values()
                if rel.kind is EnterpriseRelationshipKind.SERVICE_IMPLEMENTED_BY_REPOSITORY
                and rel.target_entity_id.root == ent_repo
            ]
            applications = [
                rel.source_entity_id.root
                for rel in relationships.values()
                if rel.kind is EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY
                and rel.target_entity_id.root == ent_repo
            ]
            for service_id in services:
                self._add(
                    relationships,
                    EnterpriseRelationshipKind.FINDING_AFFECTS_SERVICE,
                    finding_id,
                    service_id,
                    derived,
                )
            for app_id in applications:
                self._add(
                    relationships,
                    EnterpriseRelationshipKind.FINDING_AFFECTS_APPLICATION,
                    finding_id,
                    app_id,
                    derived,
                )
                for rel in relationships.values():
                    if (
                        rel.kind is EnterpriseRelationshipKind.APPLICATION_SUPPORTS_CAPABILITY
                        and rel.source_entity_id.root == app_id
                    ):
                        self._add(
                            relationships,
                            EnterpriseRelationshipKind.FINDING_AFFECTS_CAPABILITY,
                            finding_id,
                            rel.target_entity_id.root,
                            derived,
                        )

    def _propagate_recommendation_impact(
        self,
        entities: dict[str, EnterpriseEntity],
        relationships: dict[str, EnterpriseRelationship],
        cs_repo: str,
        recommendation_id: str,
        now: datetime,
    ) -> None:
        derived = EnterpriseProvenance(
            category=EnterpriseProvenanceCategory.DERIVED_RECOMMENDATION,
            derivation_rule="repository_to_service_application_capability",
            confidence="high",
            recorded_at=now,
        )
        enterprise_repos = [
            rel.source_entity_id.root
            for rel in relationships.values()
            if rel.kind is EnterpriseRelationshipKind.REPOSITORY_RESOLVES_TO_CODESTRATA_REPOSITORY
            and rel.target_entity_id.root == cs_repo
        ]
        for ent_repo in enterprise_repos:
            for rel in relationships.values():
                if (
                    rel.kind is EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY
                    and rel.target_entity_id.root == ent_repo
                ):
                    self._add(
                        relationships,
                        EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_APPLICATION,
                        recommendation_id,
                        rel.source_entity_id.root,
                        derived,
                    )

    def _add(
        self,
        relationships: dict[str, EnterpriseRelationship],
        kind: EnterpriseRelationshipKind,
        source: str,
        target: str,
        provenance: EnterpriseProvenance,
    ) -> None:
        rel_id = build_relationship_id(kind, source, target)
        if rel_id in relationships:
            return
        relationships[rel_id] = EnterpriseRelationship(
            relationship_id=EnterpriseRelationshipId(rel_id),
            kind=kind,
            source_entity_id=EnterpriseEntityId(source),
            target_entity_id=EnterpriseEntityId(target),
            provenance=provenance,
        )
