"""Contracts and exceptions for modernization assessment HTML reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aimf.ai.agents.models import ModernizationAssessmentResult
from aimf.ai.contracts.models import LLMAnalysisContext
from aimf.models import AnalysisResult


class AssessmentMode(StrEnum):
    """Execution mode for modernization assessment."""

    DETERMINISTIC = "deterministic"
    AI_ENHANCED = "ai-enhanced"


class AIExecutionStatus(StrEnum):
    """Outcome of the optional AI assessment stage."""

    NOT_EXECUTED = "not_executed"
    EXECUTED = "executed"
    FAILED = "failed"


class AssessmentTiming(BaseModel):
    """Wall-clock timing metadata for an assessment run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_ms: float = Field(ge=0.0)
    scan_ms: float | None = Field(default=None, ge=0.0)
    analysis_ms: float | None = Field(default=None, ge=0.0)
    static_analysis_ms: float | None = Field(default=None, ge=0.0)
    ai_ms: float | None = Field(default=None, ge=0.0)
    report_ms: float | None = Field(default=None, ge=0.0)


class ModernizationReportError(Exception):
    """Base error for modernization HTML report failures."""


class ModernizationReportValidationError(ModernizationReportError):
    """Raised when report input fails validation before rendering."""


class ModernizationReportInput(BaseModel):
    """Validated input for a customer-facing modernization HTML report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    analysis_result: AnalysisResult
    assessment_mode: AssessmentMode = AssessmentMode.DETERMINISTIC
    analysis_context: LLMAnalysisContext | None = None
    assessment_result: ModernizationAssessmentResult | None = None
    ai_status: AIExecutionStatus = AIExecutionStatus.NOT_EXECUTED
    ai_failure_message: str | None = None
    generated_at_utc: datetime
    report_title: str = "Modernization Assessment"
    organization_name: str | None = None
    repository_display_name: str | None = None
    repository_reference: str | None = None
    confidentiality_notice: str | None = None
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    timing: AssessmentTiming | None = None

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

    @field_validator("repository_reference")
    @classmethod
    def validate_repository_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        return compact or None

    @model_validator(mode="after")
    def validate_mode_payload(self) -> ModernizationReportInput:
        if self.assessment_mode == AssessmentMode.AI_ENHANCED:
            if self.ai_status == AIExecutionStatus.EXECUTED:
                if self.analysis_context is None:
                    raise ValueError("AI-enhanced reports require analysis_context")
                if self.assessment_result is None:
                    raise ValueError("AI-enhanced reports require assessment_result")
            elif self.ai_status == AIExecutionStatus.FAILED:
                if self.assessment_result is not None:
                    raise ValueError("Failed AI assessments must not include assessment_result")
            elif self.assessment_result is not None:
                raise ValueError("AI assessment_result requires ai_status=executed")
        elif self.assessment_result is not None:
            raise ValueError("Deterministic reports must not include assessment_result")
        return self

    @property
    def ai_executed(self) -> bool:
        return (
            self.assessment_mode == AssessmentMode.AI_ENHANCED
            and self.ai_status == AIExecutionStatus.EXECUTED
            and self.assessment_result is not None
        )
