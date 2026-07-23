"""Immutable enterprise entity and relationship domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aimf.domain.enterprise.enums import (
    EnterpriseCriticality,
    EnterpriseEntityKind,
    EnterpriseLifecycle,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
)
from aimf.domain.enterprise.identifiers import EnterpriseEntityId, EnterpriseRelationshipId


class EnterpriseProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: EnterpriseProvenanceCategory
    source_ref: str | None = None
    derivation_rule: str | None = None
    confidence: str = "exact"
    recorded_at: datetime | None = None


class EnterpriseEntity(BaseModel):
    """Canonical graph-node projection for any enterprise entity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: EnterpriseEntityId
    kind: EnterpriseEntityKind
    name: str
    description: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    provenance: EnterpriseProvenance
    lifecycle: EnterpriseLifecycle = EnterpriseLifecycle.UNKNOWN
    criticality: EnterpriseCriticality = EnterpriseCriticality.UNKNOWN


class EnterpriseRelationship(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relationship_id: EnterpriseRelationshipId
    kind: EnterpriseRelationshipKind
    source_entity_id: EnterpriseEntityId
    target_entity_id: EnterpriseEntityId
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: EnterpriseProvenance


class EnterpriseKnowledgeGraph(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    graph_id: str
    enterprise_id: str
    schema_version: str
    entities: tuple[EnterpriseEntity, ...] = ()
    relationships: tuple[EnterpriseRelationship, ...] = ()
    repository_links: tuple[str, ...] = ()
    source_fingerprint: str
    graph_fingerprint: str
    created_at: datetime
    validation_summary: dict[str, Any] = Field(default_factory=dict)
