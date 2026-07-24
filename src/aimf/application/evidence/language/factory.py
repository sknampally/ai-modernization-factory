"""Composition root for language evidence providers."""

from __future__ import annotations

from aimf.application.evidence.language.planner import LanguageEvidenceProviderPlanner
from aimf.application.evidence.language.providers import (
    JavaLanguageEvidenceProvider,
    JavaScriptLanguageEvidenceProvider,
    PythonLanguageEvidenceProvider,
)
from aimf.application.evidence.language.raw_facts import PROVIDER_PRECEDENCE
from aimf.application.evidence.language.registry import LanguageEvidenceProviderRegistry
from aimf.application.evidence.language.service import LanguageEvidenceService
from aimf.config.settings import AimfSettings, LanguageEvidenceSettings


def create_language_evidence_registry(
    settings: LanguageEvidenceSettings | None = None,
) -> LanguageEvidenceProviderRegistry:
    registry = LanguageEvidenceProviderRegistry()
    cfg = settings or LanguageEvidenceSettings()
    if cfg.python.enabled:
        registry.register(PythonLanguageEvidenceProvider())
    if cfg.java.enabled:
        registry.register(JavaLanguageEvidenceProvider())
    if cfg.javascript.enabled:
        registry.register(JavaScriptLanguageEvidenceProvider())
    return registry


def create_language_evidence_service(
    settings: AimfSettings | None = None,
) -> LanguageEvidenceService:
    evidence_settings = (
        settings.evidence.language if settings is not None else LanguageEvidenceSettings()
    )
    registry = create_language_evidence_registry(evidence_settings)
    enabled_ids: frozenset[str] | None = None
    if not evidence_settings.providers.auto_detect:
        enabled_ids = frozenset(
            provider_id
            for provider_id, enabled in (
                ("language.python.core", evidence_settings.python.enabled),
                ("language.java.core", evidence_settings.java.enabled),
                ("language.javascript.core", evidence_settings.javascript.enabled),
            )
            if enabled
        )
    else:
        # Still respect per-provider enable toggles.
        enabled_ids = frozenset(
            provider_id
            for provider_id, enabled in (
                ("language.python.core", evidence_settings.python.enabled),
                ("language.java.core", evidence_settings.java.enabled),
                ("language.javascript.core", evidence_settings.javascript.enabled),
            )
            if enabled
        )
    precedence = tuple(evidence_settings.providers.precedence) or PROVIDER_PRECEDENCE
    planner = LanguageEvidenceProviderPlanner(
        registry,
        enabled_provider_ids=enabled_ids,
        auto_detect=evidence_settings.providers.auto_detect,
        precedence=precedence,
    )
    return LanguageEvidenceService(
        registry,
        planner=planner,
        fail_fast=evidence_settings.providers.fail_fast,
    )


def language_evidence_pipeline_enabled(settings: AimfSettings | None) -> bool:
    if settings is None:
        return False
    return bool(settings.evidence.language.enabled)
