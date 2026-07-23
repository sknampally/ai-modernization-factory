"""Relationship kind constraints (source/target entity kinds)."""

from __future__ import annotations

from aimf.domain.enterprise.enums import EnterpriseEntityKind, EnterpriseRelationshipKind
from aimf.domain.enterprise.errors import EnterpriseRelationshipConstraintError

_CONSTRAINTS: dict[
    EnterpriseRelationshipKind,
    tuple[frozenset[EnterpriseEntityKind], frozenset[EnterpriseEntityKind]],
] = {
    EnterpriseRelationshipKind.ORGANIZATION_CONTAINS_ORGANIZATION: (
        frozenset({EnterpriseEntityKind.ORGANIZATION}),
        frozenset({EnterpriseEntityKind.ORGANIZATION}),
    ),
    EnterpriseRelationshipKind.ORGANIZATION_OWNS_DOMAIN: (
        frozenset({EnterpriseEntityKind.ORGANIZATION}),
        frozenset({EnterpriseEntityKind.BUSINESS_DOMAIN}),
    ),
    EnterpriseRelationshipKind.DOMAIN_CONTAINS_DOMAIN: (
        frozenset({EnterpriseEntityKind.BUSINESS_DOMAIN}),
        frozenset({EnterpriseEntityKind.BUSINESS_DOMAIN}),
    ),
    EnterpriseRelationshipKind.DOMAIN_PROVIDES_CAPABILITY: (
        frozenset({EnterpriseEntityKind.BUSINESS_DOMAIN}),
        frozenset({EnterpriseEntityKind.BUSINESS_CAPABILITY}),
    ),
    EnterpriseRelationshipKind.CAPABILITY_CONTAINS_CAPABILITY: (
        frozenset({EnterpriseEntityKind.BUSINESS_CAPABILITY}),
        frozenset({EnterpriseEntityKind.BUSINESS_CAPABILITY}),
    ),
    EnterpriseRelationshipKind.APPLICATION_SUPPORTS_CAPABILITY: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset({EnterpriseEntityKind.BUSINESS_CAPABILITY}),
    ),
    EnterpriseRelationshipKind.APPLICATION_BELONGS_TO_DOMAIN: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset({EnterpriseEntityKind.BUSINESS_DOMAIN}),
    ),
    EnterpriseRelationshipKind.APPLICATION_CONTAINS_SERVICE: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset({EnterpriseEntityKind.REPOSITORY_REFERENCE}),
    ),
    EnterpriseRelationshipKind.APPLICATION_DEPENDS_ON_APPLICATION: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.SERVICE_IMPLEMENTED_BY_REPOSITORY: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.REPOSITORY_REFERENCE}),
    ),
    EnterpriseRelationshipKind.SERVICE_EXPOSES_API: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.API}),
    ),
    EnterpriseRelationshipKind.SERVICE_CONSUMES_API: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.API}),
    ),
    EnterpriseRelationshipKind.SERVICE_DEPENDS_ON_SERVICE: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.SERVICE_READS_FROM_DATA_STORE: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.DATA_STORE}),
    ),
    EnterpriseRelationshipKind.SERVICE_WRITES_TO_DATA_STORE: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.DATA_STORE}),
    ),
    EnterpriseRelationshipKind.SERVICE_PUBLISHES_TO_CHANNEL: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.MESSAGE_CHANNEL}),
    ),
    EnterpriseRelationshipKind.SERVICE_CONSUMES_FROM_CHANNEL: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.MESSAGE_CHANNEL}),
    ),
    EnterpriseRelationshipKind.APPLICATION_DEPLOYED_TO_ENVIRONMENT: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset({EnterpriseEntityKind.ENVIRONMENT}),
    ),
    EnterpriseRelationshipKind.SERVICE_DEPLOYED_TO_ENVIRONMENT: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset({EnterpriseEntityKind.ENVIRONMENT}),
    ),
    EnterpriseRelationshipKind.RESOURCE_SUPPORTS_APPLICATION: (
        frozenset({EnterpriseEntityKind.CLOUD_RESOURCE}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.RESOURCE_SUPPORTS_SERVICE: (
        frozenset({EnterpriseEntityKind.CLOUD_RESOURCE}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.TEAM_OWNS_APPLICATION: (
        frozenset({EnterpriseEntityKind.TEAM}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.TEAM_OWNS_SERVICE: (
        frozenset({EnterpriseEntityKind.TEAM}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.TEAM_OWNS_REPOSITORY: (
        frozenset({EnterpriseEntityKind.TEAM}),
        frozenset({EnterpriseEntityKind.REPOSITORY_REFERENCE}),
    ),
    EnterpriseRelationshipKind.PERSON_OWNS_APPLICATION: (
        frozenset({EnterpriseEntityKind.PERSON}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.PERSON_OWNS_SERVICE: (
        frozenset({EnterpriseEntityKind.PERSON}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.APPLICATION_GOVERNED_BY_STANDARD: (
        frozenset({EnterpriseEntityKind.APPLICATION}),
        frozenset(
            {
                EnterpriseEntityKind.TECHNOLOGY_STANDARD,
                EnterpriseEntityKind.ARCHITECTURE_STANDARD,
            }
        ),
    ),
    EnterpriseRelationshipKind.REPOSITORY_GOVERNED_BY_STANDARD: (
        frozenset({EnterpriseEntityKind.REPOSITORY_REFERENCE}),
        frozenset(
            {
                EnterpriseEntityKind.TECHNOLOGY_STANDARD,
                EnterpriseEntityKind.ARCHITECTURE_STANDARD,
            }
        ),
    ),
    EnterpriseRelationshipKind.SERVICE_GOVERNED_BY_STANDARD: (
        frozenset({EnterpriseEntityKind.SERVICE}),
        frozenset(
            {
                EnterpriseEntityKind.TECHNOLOGY_STANDARD,
                EnterpriseEntityKind.ARCHITECTURE_STANDARD,
            }
        ),
    ),
    EnterpriseRelationshipKind.INITIATIVE_MODERNIZES_APPLICATION: (
        frozenset({EnterpriseEntityKind.MODERNIZATION_INITIATIVE}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.INITIATIVE_MODERNIZES_SERVICE: (
        frozenset({EnterpriseEntityKind.MODERNIZATION_INITIATIVE}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.INITIATIVE_MODERNIZES_REPOSITORY: (
        frozenset({EnterpriseEntityKind.MODERNIZATION_INITIATIVE}),
        frozenset({EnterpriseEntityKind.REPOSITORY_REFERENCE}),
    ),
    EnterpriseRelationshipKind.INITIATIVE_ADDRESSES_RECOMMENDATION: (
        frozenset({EnterpriseEntityKind.MODERNIZATION_INITIATIVE}),
        frozenset({EnterpriseEntityKind.CODESTRATA_RECOMMENDATION}),
    ),
    EnterpriseRelationshipKind.REPOSITORY_RESOLVES_TO_CODESTRATA_REPOSITORY: (
        frozenset({EnterpriseEntityKind.REPOSITORY_REFERENCE}),
        frozenset({EnterpriseEntityKind.CODESTRATA_REPOSITORY}),
    ),
    EnterpriseRelationshipKind.REPOSITORY_HAS_SNAPSHOT: (
        frozenset({EnterpriseEntityKind.CODESTRATA_REPOSITORY}),
        frozenset({EnterpriseEntityKind.CODESTRATA_SNAPSHOT}),
    ),
    EnterpriseRelationshipKind.SNAPSHOT_HAS_ASSESSMENT: (
        frozenset({EnterpriseEntityKind.CODESTRATA_SNAPSHOT}),
        frozenset({EnterpriseEntityKind.CODESTRATA_ASSESSMENT_RUN}),
    ),
    EnterpriseRelationshipKind.ASSESSMENT_PRODUCED_FINDING: (
        frozenset({EnterpriseEntityKind.CODESTRATA_ASSESSMENT_RUN}),
        frozenset({EnterpriseEntityKind.CODESTRATA_FINDING}),
    ),
    EnterpriseRelationshipKind.ASSESSMENT_PRODUCED_RECOMMENDATION: (
        frozenset({EnterpriseEntityKind.CODESTRATA_ASSESSMENT_RUN}),
        frozenset({EnterpriseEntityKind.CODESTRATA_RECOMMENDATION}),
    ),
    EnterpriseRelationshipKind.FINDING_AFFECTS_APPLICATION: (
        frozenset({EnterpriseEntityKind.CODESTRATA_FINDING}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.FINDING_AFFECTS_SERVICE: (
        frozenset({EnterpriseEntityKind.CODESTRATA_FINDING}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.FINDING_AFFECTS_CAPABILITY: (
        frozenset({EnterpriseEntityKind.CODESTRATA_FINDING}),
        frozenset({EnterpriseEntityKind.BUSINESS_CAPABILITY}),
    ),
    EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_APPLICATION: (
        frozenset({EnterpriseEntityKind.CODESTRATA_RECOMMENDATION}),
        frozenset({EnterpriseEntityKind.APPLICATION}),
    ),
    EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_SERVICE: (
        frozenset({EnterpriseEntityKind.CODESTRATA_RECOMMENDATION}),
        frozenset({EnterpriseEntityKind.SERVICE}),
    ),
    EnterpriseRelationshipKind.RECOMMENDATION_AFFECTS_CAPABILITY: (
        frozenset({EnterpriseEntityKind.CODESTRATA_RECOMMENDATION}),
        frozenset({EnterpriseEntityKind.BUSINESS_CAPABILITY}),
    ),
}


def validate_relationship_kinds(
    kind: EnterpriseRelationshipKind,
    source_kind: EnterpriseEntityKind,
    target_kind: EnterpriseEntityKind,
) -> None:
    if kind not in _CONSTRAINTS:
        raise EnterpriseRelationshipConstraintError(
            f"Unsupported relationship kind {kind.value}",
            reason_code="unsupported_relationship_kind",
        )
    sources, targets = _CONSTRAINTS[kind]
    if source_kind not in sources or target_kind not in targets:
        raise EnterpriseRelationshipConstraintError(
            f"Invalid endpoints for {kind.value}: {source_kind.value} -> {target_kind.value}",
            reason_code="invalid_relationship_endpoints",
        )


HIERARCHY_RELATIONSHIPS = frozenset(
    {
        EnterpriseRelationshipKind.ORGANIZATION_CONTAINS_ORGANIZATION,
        EnterpriseRelationshipKind.DOMAIN_CONTAINS_DOMAIN,
        EnterpriseRelationshipKind.CAPABILITY_CONTAINS_CAPABILITY,
    }
)
