"""Composable factory for Agent Framework instances."""

from __future__ import annotations

from aimf.application.agents.assessment_agent import AssessmentAgent
from aimf.application.agents.errors import AgentConfigurationError, AgentDependencyError
from aimf.application.agents.knowledge_agent import KnowledgeAgent
from aimf.application.agents.orchestrator import AgentOrchestrator
from aimf.application.agents.planner import AgentPlanner, DeterministicAgentPlanner
from aimf.application.agents.policies import AgentExecutionPolicy, policy_from_settings
from aimf.application.agents.validation_agent import ValidationAgent
from aimf.application.assessment.service import AssessmentApplicationService
from aimf.application.knowledge.queries.service import KnowledgeQueryService
from aimf.config.settings import AimfSettings


def create_knowledge_agent(
    query_service: KnowledgeQueryService,
    *,
    policy: AgentExecutionPolicy | None = None,
) -> KnowledgeAgent:
    return KnowledgeAgent(query_service, policy=policy)


def create_assessment_agent(
    assessment_service: AssessmentApplicationService | None = None,
    *,
    settings: AimfSettings | None = None,
) -> AssessmentAgent:
    service = assessment_service or AssessmentApplicationService()
    return AssessmentAgent(assessment_service=service, settings=settings)


def create_validation_agent(
    query_service: KnowledgeQueryService,
    *,
    policy: AgentExecutionPolicy | None = None,
) -> ValidationAgent:
    return ValidationAgent(query_service, policy=policy)


def create_agent_orchestrator(
    *,
    query_service: KnowledgeQueryService | None = None,
    assessment_service: AssessmentApplicationService | None = None,
    settings: AimfSettings | None = None,
    policy: AgentExecutionPolicy | None = None,
    planner: AgentPlanner | None = None,
    include_assessment_agent: bool = True,
) -> AgentOrchestrator:
    """Compose an :class:`AgentOrchestrator`.

    Production composition may omit injected services; tests should inject fakes.
    This factory does not open databases or call Bedrock at import time.
    """

    resolved_policy = policy if policy is not None else policy_from_settings(settings)
    try:
        # Re-validate even if callers passed a pre-built policy dict-like object.
        if not isinstance(resolved_policy, AgentExecutionPolicy):
            raise AgentConfigurationError("policy must be an AgentExecutionPolicy")
    except AgentConfigurationError:
        raise

    if query_service is None:
        if settings is None:
            raise AgentDependencyError(
                "query_service is required unless settings are provided for composition"
            )
        from aimf.infrastructure.knowledge_store import create_knowledge_query_service

        query_service = create_knowledge_query_service(settings=settings)

    knowledge = create_knowledge_agent(query_service, policy=resolved_policy)
    validation = create_validation_agent(query_service, policy=resolved_policy)
    assessment: AssessmentAgent | None = None
    if include_assessment_agent:
        assessment = create_assessment_agent(assessment_service, settings=settings)

    return AgentOrchestrator(
        knowledge_agent=knowledge,
        assessment_agent=assessment,
        validation_agent=validation,
        policy=resolved_policy,
        planner=planner or DeterministicAgentPlanner(),
    )
