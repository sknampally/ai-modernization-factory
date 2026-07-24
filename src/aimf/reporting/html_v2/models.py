"""HTML Report v2 view-model contracts.

Presentation-only models. Business logic belongs in upstream domain services;
the renderer must not invent findings, recommendations, or enrichment content.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import as_tuple, require_nonblank
from aimf.reporting.architecture.models import ArchitectureReportSection
from aimf.reporting.technical_debt.models import TechnicalDebtReportSection


class DashboardMetrics(BaseModel):
    """Scannable factual KPI values for the executive dashboard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file_count: int = Field(ge=0)
    technology_count: int = Field(ge=0)
    findings_count: int = Field(ge=0)
    recommendations_count: int = Field(ge=0)
    test_file_count: int | None = None
    has_tests: bool | None = None
    test_files_label: str = "Unknown"
    cicd_present: bool | None = None
    cicd_label: str = "Unknown"
    cloud_signal_count: int | None = None
    cloud_signals_primary: str = "Unknown"
    cloud_signals_status: str = "Unknown"
    highest_finding_severity: str = "None Detected"
    repository_size_label: str = "—"


class ReportSummary(BaseModel):
    """Executive overview cards."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_name: str
    assessment_mode: str
    assessment_mode_label: str
    technologies: tuple[str, ...] = ()
    total_findings: int = Field(ge=0)
    findings_by_severity: tuple[tuple[str, int], ...] = ()
    total_recommendations: int = Field(ge=0)
    highest_recommendation_priority: str | None = None
    ai_enrichment_status: str
    ai_enrichment_available: bool = False
    metrics: DashboardMetrics | None = None
    highest_finding_severity: str = "None Detected"

    @field_validator("repository_name", "assessment_mode", "assessment_mode_label", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="summary field")

    @field_validator("technologies", "findings_by_severity", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)


class RepositoryProfileView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    reference: str | None = None
    source_type: str
    file_count: int = Field(ge=0)
    default_branch: str | None = None

    @field_validator("name", "source_type", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="repository profile field")


class TechnologyItemView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    category: str | None = None
    version: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="technology name")


class VersionHighlightView(BaseModel):
    """Concise version/dependency highlight for the technology summary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    value: str
    kind: str = "dependency"
    detail: str | None = None

    @field_validator("label", "value", "kind", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="version highlight field")


class EvidenceView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_type: str
    source_id: str
    path: str | None = None
    excerpt: str | None = None
    node_id: str | None = None

    @field_validator("evidence_type", "source_id", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="evidence field")


class FindingView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    finding_id: str
    rule_id: str
    title: str
    description: str
    severity: str
    category: str
    affected_nodes: tuple[str, ...] = ()
    evidence: tuple[EvidenceView, ...] = ()

    @field_validator(
        "finding_id",
        "rule_id",
        "title",
        "description",
        "severity",
        "category",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="finding view field")

    @field_validator("affected_nodes", "evidence", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)


class RecommendationActionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order: int = Field(ge=1)
    title: str
    description: str
    command: str | None = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="action field")


class RecommendationView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation_id: str
    title: str
    summary: str
    rationale: str
    priority: str
    category: str
    related_finding_ids: tuple[str, ...] = ()
    affected_nodes: tuple[str, ...] = ()
    actions: tuple[RecommendationActionView, ...] = ()
    evidence: tuple[EvidenceView, ...] = ()

    @field_validator(
        "recommendation_id",
        "title",
        "summary",
        "rationale",
        "priority",
        "category",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="recommendation view field")

    @field_validator(
        "related_finding_ids",
        "affected_nodes",
        "actions",
        "evidence",
        mode="before",
    )
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)


class AiThemeView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    summary: str
    related_finding_ids: tuple[str, ...] = ()
    related_recommendation_ids: tuple[str, ...] = ()


class AiPriorityView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    rationale: str
    priority: str
    related_finding_ids: tuple[str, ...] = ()
    related_recommendation_ids: tuple[str, ...] = ()


class AiRiskView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    summary: str
    severity: str
    related_finding_ids: tuple[str, ...] = ()
    related_recommendation_ids: tuple[str, ...] = ()


class AiNextStepView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order: int = Field(ge=1)
    title: str
    summary: str
    related_finding_ids: tuple[str, ...] = ()
    related_recommendation_ids: tuple[str, ...] = ()


class AiEnrichmentView(BaseModel):
    """AI-generated interpretation; never merged into deterministic sections."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    headline: str
    narrative: str
    posture: str | None = None
    themes: tuple[AiThemeView, ...] = ()
    priorities: tuple[AiPriorityView, ...] = ()
    risks: tuple[AiRiskView, ...] = ()
    suggested_next_steps: tuple[AiNextStepView, ...] = ()
    referenced_finding_ids: tuple[str, ...] = ()
    referenced_recommendation_ids: tuple[str, ...] = ()
    provider: str
    model_id: str
    request_id: str | None = None
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    limitations: tuple[str, ...] = ()
    disclaimer: str = (
        "AI-generated interpretation. Deterministic findings and recommendations "
        "remain the source of truth."
    )


class ArtifactRefView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    relative_path: str

    @field_validator("label", "relative_path", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="artifact ref field")


class AssessmentMetadataView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    generated_at_utc: str
    report_title: str
    organization_name: str | None = None
    confidentiality_notice: str | None = None
    warnings: tuple[str, ...] = ()
    timing_total_ms: float | None = None
    timing_scan_ms: float | None = None
    timing_analysis_ms: float | None = None
    timing_ai_ms: float | None = None
    timing_report_ms: float | None = None
    ai_status: str
    model_id: str | None = None
    report_version: str = "2.0"


class AssessmentSummaryView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rules_evaluated: int = Field(ge=0)
    findings_count: int = Field(ge=0)
    recommendations_count: int = Field(ge=0)
    findings_by_severity: tuple[tuple[str, int], ...] = ()
    recommendations_by_priority: tuple[tuple[str, int], ...] = ()
    summary_text: str


class HtmlReportViewModel(BaseModel):
    """Complete presentation model for HTML Report v2."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: ReportSummary
    repository: RepositoryProfileView
    technologies: tuple[TechnologyItemView, ...] = ()
    version_highlights: tuple[VersionHighlightView, ...] = ()
    assessment_summary: AssessmentSummaryView
    findings: tuple[FindingView, ...] = ()
    recommendations: tuple[RecommendationView, ...] = ()
    ai_enrichment: AiEnrichmentView | None = None
    architecture_report: ArchitectureReportSection | None = None
    technical_debt_report: TechnicalDebtReportSection | None = None
    artifacts: tuple[ArtifactRefView, ...] = ()
    metadata: AssessmentMetadataView
    provenance_note: str = (
        "Deterministic findings and recommendations are produced by CodeStrata "
        "rules and recommendation engines. AI enrichment, when present, is "
        "interpretive only and does not modify deterministic results."
    )

    @field_validator(
        "technologies",
        "version_highlights",
        "findings",
        "recommendations",
        "artifacts",
        mode="before",
    )
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)


def severity_rank(severity: str) -> int:
    order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "informational": 4,
        "info": 4,
    }
    return order.get(severity.lower(), 99)


def priority_rank(priority: str) -> int:
    order = {
        "immediate": 0,
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    return order.get(priority.lower(), 99)


def count_by_key(items: tuple[str, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return tuple(sorted(counts.items(), key=lambda pair: (severity_rank(pair[0]), pair[0])))


def as_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})
