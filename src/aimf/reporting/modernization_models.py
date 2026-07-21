"""Contracts and exceptions for modernization assessment HTML reports."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.ai.agents.models import ModernizationAssessmentResult
from aimf.ai.contracts.models import LLMAnalysisContext
from aimf.models import AnalysisResult


class ModernizationReportError(Exception):
    """Base error for modernization HTML report failures."""


class ModernizationReportValidationError(ModernizationReportError):
    """Raised when report input fails validation before rendering."""


class ModernizationReportInput(BaseModel):
    """Validated input for a customer-facing modernization HTML report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    analysis_result: AnalysisResult
    analysis_context: LLMAnalysisContext
    assessment_result: ModernizationAssessmentResult
    generated_at_utc: datetime
    report_title: str = "Modernization Assessment"
    organization_name: str | None = None
    repository_display_name: str | None = None
    confidentiality_notice: str | None = None

    @field_validator("generated_at_utc")
    @classmethod
    def validate_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware UTC")
        return value

    @field_validator("report_title")
    @classmethod
    def validate_report_title(cls, value: str) -> str:
        compact = value.strip()
        if not compact:
            raise ValueError("report_title must be a nonempty string")
        return compact
