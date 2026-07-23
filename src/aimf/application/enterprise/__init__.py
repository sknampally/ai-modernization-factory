"""Enterprise Knowledge Graph application package."""

from __future__ import annotations

__all__ = [
    "EnterpriseKnowledgeQueryService",
    "EnterpriseKnowledgeService",
    "create_enterprise_knowledge_service",
    "create_enterprise_query_service",
    "policy_from_settings",
]


def __getattr__(name: str) -> object:
    if name == "EnterpriseKnowledgeService":
        from aimf.application.enterprise.knowledge_service import EnterpriseKnowledgeService

        return EnterpriseKnowledgeService
    if name == "EnterpriseKnowledgeQueryService":
        from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService

        return EnterpriseKnowledgeQueryService
    if name in {
        "create_enterprise_knowledge_service",
        "create_enterprise_query_service",
        "policy_from_settings",
    }:
        from aimf.application.enterprise import factory as _factory

        return getattr(_factory, name)
    raise AttributeError(name)
