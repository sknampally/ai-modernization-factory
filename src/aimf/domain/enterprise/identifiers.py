"""Stable enterprise identity helpers."""

from __future__ import annotations

import re

from pydantic import RootModel, field_validator

from aimf.domain.enterprise.enums import EnterpriseEntityKind, EnterpriseRelationshipKind
from aimf.domain.enterprise.errors import EnterpriseIdentityError

_KIND_PREFIX: dict[EnterpriseEntityKind, str] = {
    EnterpriseEntityKind.ENTERPRISE: "enterprise",
    EnterpriseEntityKind.ORGANIZATION: "organization",
    EnterpriseEntityKind.BUSINESS_DOMAIN: "domain",
    EnterpriseEntityKind.BUSINESS_CAPABILITY: "capability",
    EnterpriseEntityKind.APPLICATION: "application",
    EnterpriseEntityKind.REPOSITORY_REFERENCE: "repository",
    EnterpriseEntityKind.SERVICE: "service",
    EnterpriseEntityKind.API: "api",
    EnterpriseEntityKind.DATA_STORE: "data-store",
    EnterpriseEntityKind.MESSAGE_CHANNEL: "message-channel",
    EnterpriseEntityKind.TEAM: "team",
    EnterpriseEntityKind.PERSON: "person",
    EnterpriseEntityKind.ENVIRONMENT: "environment",
    EnterpriseEntityKind.CLOUD_RESOURCE: "cloud-resource",
    EnterpriseEntityKind.TECHNOLOGY_STANDARD: "technology-standard",
    EnterpriseEntityKind.ARCHITECTURE_STANDARD: "architecture-standard",
    EnterpriseEntityKind.MODERNIZATION_INITIATIVE: "initiative",
    EnterpriseEntityKind.CODESTRATA_REPOSITORY: "codestrata-repository",
    EnterpriseEntityKind.CODESTRATA_SNAPSHOT: "codestrata-snapshot",
    EnterpriseEntityKind.CODESTRATA_ASSESSMENT_RUN: "codestrata-assessment",
    EnterpriseEntityKind.CODESTRATA_FINDING: "codestrata-finding",
    EnterpriseEntityKind.CODESTRATA_RECOMMENDATION: "codestrata-recommendation",
}

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def normalize_local_id(value: str) -> str:
    compact = value.strip().lower()
    if not compact:
        raise EnterpriseIdentityError(
            "Entity local id must be nonempty",
            reason_code="empty_local_id",
        )
    if "/" in compact or "\\" in compact or ".." in compact:
        raise EnterpriseIdentityError(
            "Entity local id must not contain path segments",
            reason_code="unsafe_local_id",
            field_path="metadata.id",
        )
    if ":" in compact:
        raise EnterpriseIdentityError(
            "Entity local id must not contain ':'",
            reason_code="unsafe_local_id",
            field_path="metadata.id",
        )
    if not _SAFE_ID.match(compact):
        raise EnterpriseIdentityError(
            "Entity local id must be machine-safe (lowercase alnum, ._-) ",
            reason_code="invalid_local_id",
            field_path="metadata.id",
        )
    return compact


def normalize_linked_ref(value: str) -> str:
    """Normalize CodeStrata-linked refs that may include ':' or '/'."""

    compact = value.strip().lower()
    if not compact:
        raise EnterpriseIdentityError(
            "Linked ref must be nonempty",
            reason_code="empty_local_id",
        )
    if ".." in compact or "\\" in compact:
        raise EnterpriseIdentityError(
            "Linked ref must not contain path traversal",
            reason_code="unsafe_local_id",
        )
    return compact.replace("/", "__").replace(":", ".")


def kind_prefix(kind: EnterpriseEntityKind) -> str:
    return _KIND_PREFIX[kind]


def build_entity_id(kind: EnterpriseEntityKind, local_id: str) -> str:
    if kind.value.startswith("Codestrata"):
        return f"{kind_prefix(kind)}:{normalize_linked_ref(local_id)}"
    return f"{kind_prefix(kind)}:{normalize_local_id(local_id)}"


def parse_entity_id(entity_id: str) -> tuple[str, str]:
    compact = entity_id.strip()
    if ":" not in compact:
        raise EnterpriseIdentityError(
            "Enterprise entity id must include a kind prefix",
            reason_code="invalid_entity_id",
            entity_id=compact,
        )
    prefix, local = compact.split(":", 1)
    return prefix, normalize_local_id(local)


def build_relationship_id(
    kind: EnterpriseRelationshipKind,
    source_entity_id: str,
    target_entity_id: str,
    *,
    discriminator: str | None = None,
) -> str:
    base = f"rel:{kind.value}:{source_entity_id}->{target_entity_id}"
    if discriminator:
        return f"{base}:{normalize_local_id(discriminator)}"
    return base


class EnterpriseEntityId(RootModel[str]):
    root: str

    @field_validator("root", mode="before")
    @classmethod
    def validate_id(cls, value: object) -> str:
        text = str(value).strip()
        parse_entity_id(text)
        return text

    def __str__(self) -> str:
        return self.root


class EnterpriseRelationshipId(RootModel[str]):
    root: str

    @field_validator("root", mode="before")
    @classmethod
    def validate_id(cls, value: object) -> str:
        text = str(value).strip()
        if not text.startswith("rel:"):
            raise EnterpriseIdentityError(
                "Relationship id must start with rel:",
                reason_code="invalid_relationship_id",
                relationship_id=text,
            )
        return text

    def __str__(self) -> str:
        return self.root
