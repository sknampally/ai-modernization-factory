"""Immutable AI recommendation contract models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aimf.ai.recommendations.enums import (
    AIRecommendationConfidence,
    AIRecommendationEffort,
    AIRecommendationImpact,
    AIRecommendationPriority,
)

AI_RECOMMENDATION_SCHEMA_VERSION = "1.0.0"


def _sorted_unique_strings(values: list[str], *, label: str) -> list[str]:
    cleaned: list[str] = []
    for item in values:
        compact = item.strip()
        if not compact:
            raise ValueError(f"{label} must not contain blank values")
        cleaned.append(compact)
    return sorted(dict.fromkeys(cleaned), key=str.lower)


class EvidenceCoverage(BaseModel):
    """How completely the recommendations cover analyzed findings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_findings: int = Field(ge=0)
    findings_considered: int = Field(ge=0)
    findings_referenced: int = Field(ge=0)
    coverage_percentage: float = Field(ge=0.0, le=100.0)
    input_truncated: bool = False

    @model_validator(mode="after")
    def validate_consistency(self) -> EvidenceCoverage:
        if self.findings_considered > self.total_findings:
            raise ValueError("findings_considered must be less than or equal to total_findings")
        if self.findings_referenced > self.findings_considered:
            raise ValueError(
                "findings_referenced must be less than or equal to findings_considered"
            )
        if self.total_findings == 0:
            expected = 0.0
        else:
            expected = round(
                100.0 * self.findings_referenced / self.total_findings,
                2,
            )
        if round(self.coverage_percentage, 2) != expected:
            raise ValueError(
                "coverage_percentage must equal "
                "round(100 * findings_referenced / total_findings, 2) "
                f"(expected {expected})"
            )
        return self


class AIRecommendation(BaseModel):
    """A single provider-neutral modernization recommendation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    priority: AIRecommendationPriority
    effort: AIRecommendationEffort
    impact: AIRecommendationImpact
    confidence: AIRecommendationConfidence
    related_finding_ids: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)

    @field_validator("recommendation_id")
    @classmethod
    def validate_recommendation_id(cls, value: str) -> str:
        compact = value.strip()
        if not compact:
            raise ValueError("recommendation_id must be a nonempty string")
        return compact

    @field_validator("related_finding_ids", "suggested_actions", "dependencies", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return _sorted_unique_strings([str(item) for item in value], label="list")


class ModernizationPhase(BaseModel):
    """An ordered phase grouping recommendations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    phase: int = Field(ge=1)
    name: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    recommendations: list[str] = Field(default_factory=list)
    expected_outcomes: list[str] = Field(default_factory=list)

    @field_validator("recommendations", "expected_outcomes", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return _sorted_unique_strings([str(item) for item in value], label="list")


class AIRecommendationResult(BaseModel):
    """Provider-neutral AI recommendation contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = AI_RECOMMENDATION_SCHEMA_VERSION
    executive_summary: str = Field(min_length=1)
    overall_assessment: str = Field(min_length=1)
    key_risks: list[str] = Field(default_factory=list)
    recommendations: list[AIRecommendation] = Field(default_factory=list)
    modernization_phases: list[ModernizationPhase] = Field(default_factory=list)
    evidence_coverage: EvidenceCoverage
    limitations: list[str] = Field(default_factory=list)

    @field_validator("key_risks", "limitations", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return _sorted_unique_strings([str(item) for item in value], label="list")

    @field_validator("recommendations", mode="before")
    @classmethod
    def sort_recommendations(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return sorted(
            value,
            key=lambda item: (
                item.get("recommendation_id", "")
                if isinstance(item, dict)
                else getattr(item, "recommendation_id", "")
            ).lower(),
        )

    @field_validator("modernization_phases", mode="before")
    @classmethod
    def sort_phases(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return sorted(
            value,
            key=lambda item: (
                item.get("phase", 0) if isinstance(item, dict) else getattr(item, "phase", 0)
            ),
        )

    @model_validator(mode="after")
    def validate_result_integrity(self) -> AIRecommendationResult:
        recommendation_ids = [item.recommendation_id for item in self.recommendations]
        if len(recommendation_ids) != len(set(recommendation_ids)):
            raise ValueError("recommendation_id values must be unique")

        phase_numbers = [item.phase for item in self.modernization_phases]
        if len(phase_numbers) != len(set(phase_numbers)):
            raise ValueError("modernization phase numbers must be unique")
        if phase_numbers != sorted(phase_numbers):
            raise ValueError("modernization phases must be ordered by phase number")

        known_ids = set(recommendation_ids)
        for recommendation in self.recommendations:
            unknown_dependencies = sorted(set(recommendation.dependencies) - known_ids)
            if unknown_dependencies:
                raise ValueError(
                    "recommendation dependencies reference unknown recommendation IDs: "
                    + ", ".join(unknown_dependencies)
                )

        for phase in self.modernization_phases:
            unknown = sorted(set(phase.recommendations) - known_ids)
            if unknown:
                raise ValueError(
                    "modernization phases reference unknown recommendation IDs: "
                    + ", ".join(unknown)
                )

        if self.schema_version != AI_RECOMMENDATION_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {AI_RECOMMENDATION_SCHEMA_VERSION}")

        return self

    def model_dump_json_ready(self) -> dict[str, Any]:
        """Return a JSON-ready dictionary using mode='json'."""

        return self.model_dump(mode="json")
