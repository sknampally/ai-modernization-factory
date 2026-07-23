"""Application-layer errors for enterprise knowledge."""

from __future__ import annotations


class EnterpriseApplicationError(Exception):
    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        entity_id: str | None = None,
        relationship_id: str | None = None,
        field_path: str | None = None,
        manifest_path: str | None = None,
        blocking: bool = True,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.entity_id = entity_id
        self.relationship_id = relationship_id
        self.field_path = field_path
        self.manifest_path = manifest_path
        self.blocking = blocking


class EnterpriseWorkspaceNotFoundError(EnterpriseApplicationError):
    pass


class EnterpriseManifestLoadError(EnterpriseApplicationError):
    pass


class EnterpriseManifestParseError(EnterpriseApplicationError):
    pass


class EnterpriseSchemaVersionError(EnterpriseApplicationError):
    pass


class EnterpriseManifestValidationError(EnterpriseApplicationError):
    pass


class EnterpriseDuplicateEntityError(EnterpriseApplicationError):
    pass


class EnterpriseDuplicateRelationshipError(EnterpriseApplicationError):
    pass


class EnterpriseUnknownReferenceError(EnterpriseApplicationError):
    pass


class EnterpriseRepositoryResolutionError(EnterpriseApplicationError):
    pass


class EnterpriseGraphBuildError(EnterpriseApplicationError):
    pass


class EnterpriseGraphValidationError(EnterpriseApplicationError):
    pass


class EnterpriseGraphPersistenceError(EnterpriseApplicationError):
    pass


class EnterpriseGraphNotFoundError(EnterpriseApplicationError):
    pass


class EnterpriseEntityNotFoundError(EnterpriseApplicationError):
    pass


class EnterpriseQueryLimitError(EnterpriseApplicationError):
    pass


class EnterpriseTraversalLimitError(EnterpriseApplicationError):
    pass


class EnterpriseSecurityError(EnterpriseApplicationError):
    pass
