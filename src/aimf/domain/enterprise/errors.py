"""Enterprise Knowledge Graph domain errors."""

from __future__ import annotations


class EnterpriseDomainError(Exception):
    """Base domain error for enterprise knowledge."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        entity_id: str | None = None,
        relationship_id: str | None = None,
        field_path: str | None = None,
        blocking: bool = True,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.entity_id = entity_id
        self.relationship_id = relationship_id
        self.field_path = field_path
        self.blocking = blocking


class EnterpriseIdentityError(EnterpriseDomainError):
    """Invalid or colliding enterprise identity."""


class EnterpriseRelationshipConstraintError(EnterpriseDomainError):
    """Relationship source/target kinds are incompatible."""


class EnterpriseHierarchyCycleError(EnterpriseDomainError):
    """Hierarchy contains a cycle."""
