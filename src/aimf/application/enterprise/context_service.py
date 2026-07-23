"""Compose repository knowledge with enterprise context (no circular deps)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from aimf.application.enterprise.errors import (
    EnterpriseApplicationError,
    EnterpriseEntityNotFoundError,
    EnterpriseGraphNotFoundError,
)
from aimf.application.enterprise.models import EnterpriseEntityView, EnterpriseImpactSummary
from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.domain.enterprise.enums import EnterpriseEntityKind, EnterpriseRelationshipKind


class EnterpriseAssessmentContext(BaseModel):
    """Optional enrichment for assessments; does not alter finding IDs or rules."""

    model_config = ConfigDict(frozen=True)

    repository_entity_id: str | None = None
    applications: tuple[EnterpriseEntityView, ...] = ()
    services: tuple[EnterpriseEntityView, ...] = ()
    capabilities: tuple[EnterpriseEntityView, ...] = ()
    owning_teams: tuple[EnterpriseEntityView, ...] = ()
    standards: tuple[EnterpriseEntityView, ...] = ()
    environments: tuple[EnterpriseEntityView, ...] = ()
    initiatives: tuple[EnterpriseEntityView, ...] = ()
    criticality: str | None = None
    limitations: tuple[str, ...] = Field(default_factory=tuple)


class EnterpriseContextQueryService:
    """Cross-layer queries: enterprise context for repository knowledge IDs."""

    def __init__(
        self,
        enterprise_queries: EnterpriseKnowledgeQueryService,
        *,
        enterprise_id: str = "enterprise:acme",
    ) -> None:
        self._enterprise = enterprise_queries
        self._enterprise_id = enterprise_id

    def get_repository_context(self, repository_entity_id: str) -> EnterpriseImpactSummary:
        return self._enterprise.repository_context(
            repository_entity_id,
            enterprise_id=self._enterprise_id,
        )

    def get_finding_enterprise_impact(self, finding_entity_id: str) -> EnterpriseImpactSummary:
        return self._enterprise.finding_impact(
            finding_entity_id,
            enterprise_id=self._enterprise_id,
        )

    def get_recommendation_enterprise_impact(
        self,
        recommendation_entity_id: str,
    ) -> EnterpriseImpactSummary:
        return self._enterprise.recommendation_impact(
            recommendation_entity_id,
            enterprise_id=self._enterprise_id,
        )


class EnterpriseAssessmentContextProvider:
    """Future Analysis Intelligence boundary; retrieval only in Phase 3."""

    def __init__(
        self,
        enterprise_queries: EnterpriseKnowledgeQueryService,
        *,
        enterprise_id: str = "enterprise:acme",
    ) -> None:
        self._queries = enterprise_queries
        self._enterprise_id = enterprise_id

    def get_context_for_repository(self, repository_entity_id: str) -> EnterpriseAssessmentContext:
        try:
            summary = self._queries.repository_context(
                repository_entity_id,
                enterprise_id=self._enterprise_id,
            )
        except (
            EnterpriseGraphNotFoundError,
            EnterpriseEntityNotFoundError,
            EnterpriseApplicationError,
        ):
            return EnterpriseAssessmentContext(
                repository_entity_id=repository_entity_id,
                limitations=("Enterprise graph unavailable or repository not linked",),
            )

        applications = tuple(
            item
            for item in summary.impacted_entities
            if item.kind is EnterpriseEntityKind.APPLICATION
        )
        services = tuple(
            item
            for item in summary.impacted_entities
            if item.kind is EnterpriseEntityKind.SERVICE
        )
        capabilities = tuple(
            item
            for item in summary.impacted_entities
            if item.kind is EnterpriseEntityKind.BUSINESS_CAPABILITY
        )
        teams: list[EnterpriseEntityView] = []
        standards: list[EnterpriseEntityView] = []
        environments: list[EnterpriseEntityView] = []
        initiatives: list[EnterpriseEntityView] = []
        for app in applications:
            teams.extend(
                self._queries.list_by_relationship(
                    target_id=app.entity_id,
                    kind=EnterpriseRelationshipKind.TEAM_OWNS_APPLICATION,
                    enterprise_id=self._enterprise_id,
                )
            )
            standards.extend(
                self._queries.list_by_relationship(
                    source_id=app.entity_id,
                    kind=EnterpriseRelationshipKind.APPLICATION_GOVERNED_BY_STANDARD,
                    enterprise_id=self._enterprise_id,
                )
            )
            environments.extend(
                self._queries.list_by_relationship(
                    source_id=app.entity_id,
                    kind=EnterpriseRelationshipKind.APPLICATION_DEPLOYED_TO_ENVIRONMENT,
                    enterprise_id=self._enterprise_id,
                )
            )
            initiatives.extend(
                self._queries.list_by_relationship(
                    target_id=app.entity_id,
                    kind=EnterpriseRelationshipKind.INITIATIVE_MODERNIZES_APPLICATION,
                    enterprise_id=self._enterprise_id,
                )
            )

        criticality = None
        if applications:
            criticality = applications[0].criticality

        return EnterpriseAssessmentContext(
            repository_entity_id=repository_entity_id,
            applications=applications,
            services=services,
            capabilities=capabilities,
            owning_teams=_dedupe(teams),
            standards=_dedupe(standards),
            environments=_dedupe(environments),
            initiatives=_dedupe(initiatives),
            criticality=criticality,
            limitations=summary.limitations,
        )


def _dedupe(items: list[EnterpriseEntityView]) -> tuple[EnterpriseEntityView, ...]:
    return tuple(
        sorted(
            {item.entity_id: item for item in items}.values(),
            key=lambda item: item.entity_id,
        )
    )
