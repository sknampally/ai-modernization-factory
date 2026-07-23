"""Shared Rule Platform application package (Phase 4.1)."""

from __future__ import annotations

__all__ = [
    "LegacyRuleAdapter",
    "RuleAnalysisService",
    "RuleExecutionFacade",
    "RuleRegistry",
    "RuleTestHarness",
    "create_rule_analysis_service",
    "policy_from_settings",
]


def __getattr__(name: str) -> object:
    if name == "RuleAnalysisService":
        from aimf.application.rules.analysis_service import RuleAnalysisService

        return RuleAnalysisService
    if name == "RuleRegistry":
        from aimf.application.rules.registry import RuleRegistry

        return RuleRegistry
    if name == "RuleTestHarness":
        from aimf.application.rules.testing import RuleTestHarness

        return RuleTestHarness
    if name == "RuleExecutionFacade":
        from aimf.application.rules.facade import RuleExecutionFacade

        return RuleExecutionFacade
    if name == "LegacyRuleAdapter":
        from aimf.application.rules.legacy_adapter import LegacyRuleAdapter

        return LegacyRuleAdapter
    if name in {"create_rule_analysis_service", "policy_from_settings"}:
        from aimf.application.rules import factory as _factory

        return getattr(_factory, name)
    raise AttributeError(name)
