"""Composition root for architecture conclusions."""

from __future__ import annotations

from aimf.application.architecture.conclusions.policies import default_conclusion_policies
from aimf.application.architecture.conclusions.registry import (
    ArchitectureConclusionPolicyRegistry,
)
from aimf.application.architecture.conclusions.result import ArchitectureConclusionResult
from aimf.application.architecture.conclusions.service import ArchitectureConclusionService
from aimf.config.settings import AimfSettings, ArchitectureConclusionsSettings


def create_conclusion_policy_registry(
    settings: ArchitectureConclusionsSettings | None = None,
) -> ArchitectureConclusionPolicyRegistry:
    _ = settings
    registry = ArchitectureConclusionPolicyRegistry()
    for policy in default_conclusion_policies():
        registry.register(policy)  # type: ignore[arg-type]
    return registry


def create_architecture_conclusion_service(
    settings: AimfSettings | None = None,
) -> ArchitectureConclusionService:
    conclusion_settings = (
        settings.analysis.architecture_conclusions
        if settings is not None
        else ArchitectureConclusionsSettings()
    )
    registry = create_conclusion_policy_registry(conclusion_settings)
    return ArchitectureConclusionService(registry)


def architecture_conclusions_enabled(settings: AimfSettings | None) -> bool:
    if settings is None:
        return False
    return bool(settings.analysis.architecture_conclusions.enabled)


def enabled_policy_ids(settings: AimfSettings) -> frozenset[str]:
    cfg = settings.analysis.architecture_conclusions.policies
    mapping = {
        "architecture.conclusion.boundary-integrity": cfg.boundary_integrity,
        "architecture.conclusion.cyclic-dependency-structure": cfg.cyclic_dependency_structure,
        "architecture.conclusion.broad-dependency-surface": cfg.broad_dependency_surface,
        "architecture.conclusion.framework-boundary-erosion": cfg.framework_boundary_erosion,
        "architecture.conclusion.enterprise-nonconformance": cfg.enterprise_nonconformance,
        "architecture.conclusion.positive-boundary-conformance": (
            cfg.positive_boundary_conformance
        ),
        "architecture.conclusion.insufficient-evidence": cfg.insufficient_evidence,
    }
    return frozenset(policy_id for policy_id, enabled in mapping.items() if enabled)


def empty_conclusion_result() -> ArchitectureConclusionResult:
    return ArchitectureConclusionResult(enabled=False)
