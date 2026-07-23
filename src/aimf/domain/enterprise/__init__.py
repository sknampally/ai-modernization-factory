"""Enterprise Knowledge Graph domain package.

This is distinct from ``aimf.domain.engineering_knowledge`` (technology concepts).
Enterprise models describe organizations, applications, ownership, and
cross-repository architecture context declared in YAML manifests.
"""

from __future__ import annotations

from aimf.domain.enterprise.entities import (
    EnterpriseEntity,
    EnterpriseKnowledgeGraph,
    EnterpriseProvenance,
    EnterpriseRelationship,
)
from aimf.domain.enterprise.enums import (
    ApplicationKind,
    EnterpriseCriticality,
    EnterpriseEntityKind,
    EnterpriseLifecycle,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
    EnvironmentKind,
    InitiativeStatus,
    ServiceKind,
    StandardStatus,
    UnknownFieldPolicy,
)
from aimf.domain.enterprise.errors import (
    EnterpriseDomainError,
    EnterpriseHierarchyCycleError,
    EnterpriseIdentityError,
    EnterpriseRelationshipConstraintError,
)
from aimf.domain.enterprise.identifiers import (
    EnterpriseEntityId,
    EnterpriseRelationshipId,
    build_entity_id,
    build_relationship_id,
    normalize_local_id,
)
from aimf.domain.enterprise.manifests import (
    SUPPORTED_API_VERSION,
    EnterpriseManifestCollection,
    EnterpriseManifestDocument,
    ManifestMetadata,
)
from aimf.domain.enterprise.relationships import (
    HIERARCHY_RELATIONSHIPS,
    validate_relationship_kinds,
)

__all__ = [
    "SUPPORTED_API_VERSION",
    "ApplicationKind",
    "EnterpriseCriticality",
    "EnterpriseDomainError",
    "EnterpriseEntity",
    "EnterpriseEntityId",
    "EnterpriseEntityKind",
    "EnterpriseHierarchyCycleError",
    "EnterpriseIdentityError",
    "EnterpriseKnowledgeGraph",
    "EnterpriseLifecycle",
    "EnterpriseManifestCollection",
    "EnterpriseManifestDocument",
    "EnterpriseProvenance",
    "EnterpriseProvenanceCategory",
    "EnterpriseRelationship",
    "EnterpriseRelationshipConstraintError",
    "EnterpriseRelationshipId",
    "EnterpriseRelationshipKind",
    "EnvironmentKind",
    "HIERARCHY_RELATIONSHIPS",
    "InitiativeStatus",
    "ManifestMetadata",
    "ServiceKind",
    "StandardStatus",
    "UnknownFieldPolicy",
    "build_entity_id",
    "build_relationship_id",
    "normalize_local_id",
    "validate_relationship_kinds",
]
