"""Application language evidence package."""

from aimf.application.evidence.language.factory import (
    create_language_evidence_service,
    language_evidence_pipeline_enabled,
)
from aimf.application.evidence.language.service import LanguageEvidenceService

__all__ = [
    "LanguageEvidenceService",
    "create_language_evidence_service",
    "language_evidence_pipeline_enabled",
]
