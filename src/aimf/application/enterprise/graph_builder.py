"""Build EnterpriseKnowledgeGraph from validated manifests."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from aimf.application.enterprise.errors import EnterpriseGraphBuildError
from aimf.application.enterprise.models import EnterprisePolicy
from aimf.application.enterprise.ports import RepositoryIdentityResolver
from aimf.domain.enterprise.entities import (
    EnterpriseEntity,
    EnterpriseKnowledgeGraph,
    EnterpriseProvenance,
    EnterpriseRelationship,
)
from aimf.domain.enterprise.enums import (
    EnterpriseCriticality,
    EnterpriseEntityKind,
    EnterpriseLifecycle,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
)
from aimf.domain.enterprise.identifiers import (
    EnterpriseEntityId,
    EnterpriseRelationshipId,
    build_entity_id,
    build_relationship_id,
)
from aimf.domain.enterprise.manifests import EnterpriseManifestCollection
from aimf.domain.enterprise.relationships import validate_relationship_kinds

_INLINE_RELS: tuple[tuple[str, EnterpriseEntityKind, EnterpriseRelationshipKind], ...] = (
    (
        "businessDomains",
        EnterpriseEntityKind.BUSINESS_DOMAIN,
        EnterpriseRelationshipKind.APPLICATION_BELONGS_TO_DOMAIN,
    ),
    (
        "capabilities",
        EnterpriseEntityKind.BUSINESS_CAPABILITY,
        EnterpriseRelationshipKind.APPLICATION_SUPPORTS_CAPABILITY,
    ),
    (
        "repositories",
        EnterpriseEntityKind.REPOSITORY_REFERENCE,
        EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
    ),
    (
        "services",
        EnterpriseEntityKind.SERVICE,
        EnterpriseRelationshipKind.APPLICATION_CONTAINS_SERVICE,
    ),
    (
        "apis",
        EnterpriseEntityKind.API,
        EnterpriseRelationshipKind.SERVICE_EXPOSES_API,
    ),
    (
        "dataStores",
        EnterpriseEntityKind.DATA_STORE,
        EnterpriseRelationshipKind.SERVICE_READS_FROM_DATA_STORE,
    ),
    (
        "environments",
        EnterpriseEntityKind.ENVIRONMENT,
        EnterpriseRelationshipKind.APPLICATION_DEPLOYED_TO_ENVIRONMENT,
    ),
)

_SCALAR_RELS: tuple[tuple[str, EnterpriseEntityKind, EnterpriseRelationshipKind], ...] = (
    (
        "owningTeam",
        EnterpriseEntityKind.TEAM,
        EnterpriseRelationshipKind.TEAM_OWNS_APPLICATION,
    ),
    (
        "parentOrganization",
        EnterpriseEntityKind.ORGANIZATION,
        EnterpriseRelationshipKind.ORGANIZATION_CONTAINS_ORGANIZATION,
    ),
    (
        "parentDomain",
        EnterpriseEntityKind.BUSINESS_DOMAIN,
        EnterpriseRelationshipKind.DOMAIN_CONTAINS_DOMAIN,
    ),
    (
        "parentCapability",
        EnterpriseEntityKind.BUSINESS_CAPABILITY,
        EnterpriseRelationshipKind.CAPABILITY_CONTAINS_CAPABILITY,
    ),
)


class EnterpriseGraphBuilder:
    """Build an immutable enterprise graph from typed validated manifests."""

    def build(
        self,
        collection: EnterpriseManifestCollection,
        *,
        policy: EnterprisePolicy,
        resolver: RepositoryIdentityResolver | None = None,
        enterprise_id: str | None = None,
    ) -> EnterpriseKnowledgeGraph:
        entities: dict[str, EnterpriseEntity] = {}
        relationships: dict[str, EnterpriseRelationship] = {}
        repository_links: list[str] = []
        now = datetime.now(UTC)
        declared = EnterpriseProvenance(
            category=EnterpriseProvenanceCategory.DECLARED_YAML,
            source_ref=collection.workspace_relative_root,
            derivation_rule=None,
            confidence="exact",
            recorded_at=now,
        )
        resolved_prov = EnterpriseProvenance(
            category=EnterpriseProvenanceCategory.RESOLVED_REPOSITORY_REGISTRY,
            derivation_rule="repository_registry_resolve",
            confidence="exact",
            recorded_at=now,
        )

        root_enterprise_id = enterprise_id
        # Pass 1: materialize entities (and resolved CodeStrata repository nodes).
        for doc in collection.documents:
            kind_raw = str(doc.kind)
            if kind_raw == "Relationships":
                continue
            if kind_raw == EnterpriseEntityKind.ENTERPRISE.value:
                root_enterprise_id = build_entity_id(
                    EnterpriseEntityKind.ENTERPRISE, doc.metadata.id
                )

            kind = EnterpriseEntityKind(kind_raw)
            entity_id = build_entity_id(kind, doc.metadata.id)
            attrs = {key: value for key, value in doc.spec.items() if not str(key).startswith("_")}
            entities[entity_id] = EnterpriseEntity(
                entity_id=EnterpriseEntityId(entity_id),
                kind=kind,
                name=doc.metadata.name,
                description=doc.metadata.description,
                labels=dict(doc.metadata.labels),
                annotations=dict(doc.metadata.annotations),
                attributes=attrs,
                provenance=declared.model_copy(update={"source_ref": doc.source_relative_path}),
                lifecycle=_lifecycle(doc.spec.get("lifecycle")),
                criticality=_criticality(doc.spec.get("criticality")),
            )

            if kind is EnterpriseEntityKind.REPOSITORY_REFERENCE and resolver is not None:
                ref = str(
                    doc.spec.get("canonicalKey") or doc.spec.get("remoteUrl") or doc.metadata.id
                )
                resolved = resolver.resolve(ref)
                if resolved:
                    cs_id = build_entity_id(
                        EnterpriseEntityKind.CODESTRATA_REPOSITORY, resolved
                    )
                    entities[cs_id] = EnterpriseEntity(
                        entity_id=EnterpriseEntityId(cs_id),
                        kind=EnterpriseEntityKind.CODESTRATA_REPOSITORY,
                        name=resolved,
                        provenance=resolved_prov,
                    )
                    repository_links.append(f"{entity_id}->{cs_id}")

        # Pass 2: declared relationships from entity specs and relationship docs.
        for doc in collection.documents:
            kind_raw = str(doc.kind)
            if kind_raw == "Relationships":
                continue
            kind = EnterpriseEntityKind(kind_raw)
            entity_id = build_entity_id(kind, doc.metadata.id)
            provenance = declared.model_copy(update={"source_ref": doc.source_relative_path})

            if kind is EnterpriseEntityKind.APPLICATION:
                for field, target_kind, rel_kind in _INLINE_RELS:
                    if field in {"apis", "dataStores"}:
                        continue
                    for item in doc.spec.get(field, []) or []:
                        target_id = build_entity_id(target_kind, str(item))
                        self._add_rel(
                            relationships,
                            rel_kind,
                            entity_id,
                            target_id,
                            provenance,
                            entities,
                        )
                team = doc.spec.get("owningTeam")
                if team:
                    team_id = build_entity_id(EnterpriseEntityKind.TEAM, str(team))
                    self._add_rel(
                        relationships,
                        EnterpriseRelationshipKind.TEAM_OWNS_APPLICATION,
                        team_id,
                        entity_id,
                        provenance,
                        entities,
                    )

            if kind is EnterpriseEntityKind.SERVICE:
                for field, target_kind, rel_kind in (
                    (
                        "repositories",
                        EnterpriseEntityKind.REPOSITORY_REFERENCE,
                        EnterpriseRelationshipKind.SERVICE_IMPLEMENTED_BY_REPOSITORY,
                    ),
                    (
                        "apis",
                        EnterpriseEntityKind.API,
                        EnterpriseRelationshipKind.SERVICE_EXPOSES_API,
                    ),
                    (
                        "dataStores",
                        EnterpriseEntityKind.DATA_STORE,
                        EnterpriseRelationshipKind.SERVICE_READS_FROM_DATA_STORE,
                    ),
                    (
                        "dependsOn",
                        EnterpriseEntityKind.SERVICE,
                        EnterpriseRelationshipKind.SERVICE_DEPENDS_ON_SERVICE,
                    ),
                ):
                    for item in doc.spec.get(field, []) or []:
                        target_id = build_entity_id(target_kind, str(item))
                        self._add_rel(
                            relationships,
                            rel_kind,
                            entity_id,
                            target_id,
                            provenance,
                            entities,
                        )

            if kind is EnterpriseEntityKind.REPOSITORY_REFERENCE:
                for link in repository_links:
                    if link.startswith(f"{entity_id}->"):
                        cs_id = link.split("->", 1)[1]
                        self._add_rel(
                            relationships,
                            EnterpriseRelationshipKind.REPOSITORY_RESOLVES_TO_CODESTRATA_REPOSITORY,
                            entity_id,
                            cs_id,
                            resolved_prov,
                            entities,
                        )

            for field, target_kind, rel_kind in _SCALAR_RELS:
                value = doc.spec.get(field)
                if not value:
                    continue
                if field.startswith("parent"):
                    parent_id = build_entity_id(target_kind, str(value))
                    self._add_rel(
                        relationships, rel_kind, parent_id, entity_id, provenance, entities
                    )

        for doc in collection.documents:
            if str(doc.kind) != "Relationships":
                continue
            for entry in doc.spec.get("relationships", []) or []:
                if not isinstance(entry, dict):
                    continue
                rel_kind = EnterpriseRelationshipKind(str(entry["kind"]))
                source = str(entry["source"])
                target = str(entry["target"])
                disc = entry.get("discriminator")
                self._add_rel(
                    relationships,
                    rel_kind,
                    source,
                    target,
                    declared.model_copy(update={"source_ref": doc.source_relative_path}),
                    entities,
                    discriminator=str(disc) if disc else None,
                    metadata=dict(entry.get("metadata") or {}),
                )

        if not root_enterprise_id:
            raise EnterpriseGraphBuildError(
                "Enterprise root manifest is required",
                reason_code="missing_enterprise_root",
            )

        ordered_entities = tuple(sorted(entities.values(), key=lambda item: str(item.entity_id)))
        ordered_relationships = tuple(
            sorted(relationships.values(), key=lambda item: str(item.relationship_id))
        )
        if len(ordered_entities) > policy.max_graph_entities:
            raise EnterpriseGraphBuildError(
                "Enterprise graph exceeds max_graph_entities",
                reason_code="graph_entity_limit",
            )
        if len(ordered_relationships) > policy.max_graph_relationships:
            raise EnterpriseGraphBuildError(
                "Enterprise graph exceeds max_graph_relationships",
                reason_code="graph_relationship_limit",
            )

        payload = {
            "enterprise_id": root_enterprise_id,
            "entities": [e.model_dump(mode="json") for e in ordered_entities],
            "relationships": [r.model_dump(mode="json") for r in ordered_relationships],
        }
        graph_fp = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return EnterpriseKnowledgeGraph(
            graph_id=str(uuid4()),
            enterprise_id=root_enterprise_id,
            schema_version=policy.schema_version,
            entities=ordered_entities,
            relationships=ordered_relationships,
            repository_links=tuple(sorted(repository_links)),
            source_fingerprint=collection.source_fingerprint,
            graph_fingerprint=graph_fp,
            created_at=now,
            validation_summary={
                "entity_count": len(ordered_entities),
                "relationship_count": len(ordered_relationships),
            },
        )

    def _add_rel(
        self,
        relationships: dict[str, EnterpriseRelationship],
        kind: EnterpriseRelationshipKind,
        source: str,
        target: str,
        provenance: EnterpriseProvenance,
        entities: dict[str, EnterpriseEntity],
        *,
        discriminator: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if source not in entities or target not in entities:
            return
        validate_relationship_kinds(kind, entities[source].kind, entities[target].kind)
        rel_id = build_relationship_id(kind, source, target, discriminator=discriminator)
        if rel_id in relationships:
            return
        relationships[rel_id] = EnterpriseRelationship(
            relationship_id=EnterpriseRelationshipId(rel_id),
            kind=kind,
            source_entity_id=EnterpriseEntityId(source),
            target_entity_id=EnterpriseEntityId(target),
            metadata=metadata or {},
            provenance=provenance,
        )


def _lifecycle(value: object) -> EnterpriseLifecycle:
    if value is None:
        return EnterpriseLifecycle.UNKNOWN
    try:
        return EnterpriseLifecycle(str(value))
    except ValueError:
        return EnterpriseLifecycle.UNKNOWN


def _criticality(value: object) -> EnterpriseCriticality:
    if value is None:
        return EnterpriseCriticality.UNKNOWN
    try:
        return EnterpriseCriticality(str(value))
    except ValueError:
        return EnterpriseCriticality.UNKNOWN
