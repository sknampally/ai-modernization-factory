"""Composition helpers for Shared Rule Platform."""

from __future__ import annotations

from aimf.application.rules.analysis_service import RuleAnalysisService
from aimf.application.rules.registry import RuleRegistry
from aimf.config.settings import AimfSettings
from aimf.domain.rules.applicability import RuleSuppression
from aimf.domain.rules.context import RuleExecutionPolicy


def policy_from_settings(settings: AimfSettings | None) -> RuleExecutionPolicy:
    if settings is None or getattr(settings, "rules", None) is None:
        return RuleExecutionPolicy()
    section = settings.rules
    return RuleExecutionPolicy(
        fail_on_rule_error=bool(section.fail_on_rule_error),
        max_matches_per_rule=int(section.max_matches_per_rule),
        max_total_matches=int(section.max_total_matches),
        max_evidence_per_match=int(section.max_evidence_per_match),
        max_rules_per_run=int(section.max_rules_per_run),
        claim_reuse=False,
    )


def create_empty_rule_registry() -> RuleRegistry:
    return RuleRegistry()


def create_rule_analysis_service(
    *,
    settings: AimfSettings | None = None,
    registry: RuleRegistry | None = None,
    suppressions: tuple[RuleSuppression, ...] = (),
    include_fixture_rules: bool = False,
) -> RuleAnalysisService:
    """Create a service. Production registry is empty until Phase 4.2+ packs register."""

    resolved = registry or RuleRegistry()
    if include_fixture_rules:
        from aimf.application.rules.fixtures import fixture_rules

        resolved.register_collection(fixture_rules(), production=False)  # type: ignore[arg-type]
    _ = settings  # policy applied at context build time by callers
    return RuleAnalysisService(registry=resolved, suppressions=suppressions)
