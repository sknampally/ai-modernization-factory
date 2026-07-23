"""Application DTOs for enterprise knowledge."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph
from aimf.domain.enterprise.enums import EnterpriseEntityKind, EnterpriseRelationshipKind


class EnterpriseValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class EnterpriseValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: EnterpriseValidationSeverity
    safe_message: str
    manifest_path: str | None = None
    field_path: str | None = None
    entity_id: str | None = None
    relationship_id: str | None = None
    blocking: bool = True


class EnterpriseManifestValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: str
    manifests_checked: int = 0
    entities_checked: int = 0
    relationships_checked: int = 0
    errors: tuple[EnterpriseValidationIssue, ...] = ()
    warnings: tuple[EnterpriseValidationIssue, ...] = ()
    unresolved_repository_references: tuple[str, ...] = ()
    duplicate_ids: tuple[str, ...] = ()
    cycles: tuple[str, ...] = ()
    source_fingerprint: str = ""


class EnterpriseBuildResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    graph: EnterpriseKnowledgeGraph
    validation: EnterpriseManifestValidationResult
    linked_repository_count: int = 0
    linked_assessment_count: int = 0
    duration_ms: int = 0


class EnterpriseEntityView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: str
    kind: EnterpriseEntityKind
    name: str
    description: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    provenance_category: str
    lifecycle: str | None = None
    criticality: str | None = None


class EnterpriseRelationshipView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relationship_id: str
    kind: EnterpriseRelationshipKind
    source_entity_id: str
    target_entity_id: str
    provenance_category: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnterpriseNeighborhood(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity: EnterpriseEntityView
    relationships: tuple[EnterpriseRelationshipView, ...] = ()
    neighbors: tuple[EnterpriseEntityView, ...] = ()
    truncated: bool = False
    depth: int = 1


class EnterpriseImpactSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_entity_id: str
    impacted_entities: tuple[EnterpriseEntityView, ...] = ()
    paths: tuple[tuple[str, ...], ...] = ()
    declared_count: int = 0
    derived_count: int = 0
    truncated: bool = False
    limitations: tuple[str, ...] = ()


class EnterpriseGraphDiff(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    left_graph_id: str
    right_graph_id: str
    entities_added: tuple[str, ...] = ()
    entities_removed: tuple[str, ...] = ()
    entities_modified: tuple[str, ...] = ()
    relationships_added: tuple[str, ...] = ()
    relationships_removed: tuple[str, ...] = ()
    relationships_modified: tuple[str, ...] = ()
    repository_resolutions_changed: tuple[str, ...] = ()


class EnterprisePolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = False
    workspace: str = "enterprise"
    schema_version: str = "codestrata.io/v1alpha1"
    persist_graph: bool = True
    link_repository_assessments: bool = True
    require_registered_repositories: bool = True
    allow_unresolved_repositories: bool = False
    unknown_fields: str = "error"
    max_manifest_files: int = Field(default=5000, ge=1)
    max_manifest_size_bytes: int = Field(default=1_048_576, ge=1024)
    max_yaml_depth: int = Field(default=50, ge=1, le=200)
    max_graph_entities: int = Field(default=100_000, ge=1)
    max_graph_relationships: int = Field(default=500_000, ge=1)
    max_query_results: int = Field(default=500, ge=1, le=10_000)
    max_traversal_depth: int = Field(default=5, ge=1, le=10)
    max_dependency_paths: int = Field(default=100, ge=1, le=1000)
    persist_manifest_snapshot: bool = True


class EnterpriseWorkspaceInitResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: str
    files_created: tuple[str, ...] = ()
    validated: bool = False
    created_at: datetime
