"""Validation and view helpers for modernization assessment reports."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from aimf.ai.agents.models import AGENT_VERSION, ModernizationAssessmentResult
from aimf.ai.contracts.models import LLM_CONTRACT_SCHEMA_VERSION, LLMAnalysisContext
from aimf.ai.recommendations.models import (
    AI_RECOMMENDATION_SCHEMA_VERSION,
    AIRecommendationResult,
)
from aimf.ai.recommendations.validation import (
    AIRecommendationValidationError,
    finding_ids_from_context,
    validate_recommendation_result,
)
from aimf.models import AnalysisResult, Finding, Severity
from aimf.reporting.modernization_models import (
    ModernizationReportInput,
    ModernizationReportValidationError,
)

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

SEVERITY_NAME_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def validate_modernization_report_input(
    report_input: ModernizationReportInput,
) -> ModernizationReportInput:
    """Validate cross-contract consistency before HTML rendering."""

    analysis_name = report_input.analysis_result.repository.name.strip()
    context_name = report_input.analysis_context.repository.name.strip()
    if analysis_name != context_name:
        raise ModernizationReportValidationError(
            "Inconsistent repository identifiers between AnalysisResult "
            f"('{analysis_name}') and LLMAnalysisContext ('{context_name}')"
        )

    recommendation_result = report_input.assessment_result.recommendation_result
    try:
        validate_recommendation_result(
            recommendation_result,
            report_input.analysis_context,
        )
    except AIRecommendationValidationError as error:
        raise ModernizationReportValidationError(str(error)) from error

    available_finding_ids = finding_ids_from_context(report_input.analysis_context)
    _assert_recommendation_finding_links(recommendation_result, available_finding_ids)
    _assert_phase_recommendation_links(recommendation_result)
    return report_input


def repository_identifier(report_input: ModernizationReportInput) -> str:
    """Return the display repository identifier for the report."""

    if report_input.repository_display_name and report_input.repository_display_name.strip():
        return report_input.repository_display_name.strip()
    return report_input.analysis_context.repository.name


def sorted_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Return findings in stable severity/category/rule order."""

    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER.get(finding.severity, 99),
            str(getattr(finding.category, "value", finding.category)).lower(),
            (finding.rule_id or "").lower(),
            finding.title.lower(),
        ),
    )


def finding_anchor_id(rule_id: str | None, *, index: int = 0) -> str:
    """Return a stable HTML fragment id for a finding."""

    base = _slug(rule_id or "finding")
    if index <= 0:
        return f"finding-{base}"
    return f"finding-{base}-{index + 1}"


def finding_anchor_map(findings: Iterable[Finding]) -> dict[str, str]:
    """Map rule_id -> primary fragment id for recommendation links."""

    anchors: dict[str, str] = {}
    counts: dict[str, int] = {}
    for finding in sorted_findings(findings):
        rule_id = finding.rule_id
        if not rule_id:
            continue
        key = rule_id
        occurrence = counts.get(key, 0)
        counts[key] = occurrence + 1
        if key not in anchors:
            anchors[key] = finding_anchor_id(rule_id, index=occurrence)
    return anchors


def sanitize_display_path(path: str) -> str:
    """Prefer repository-relative paths; never expose absolute filesystem paths."""

    compact = path.strip()
    if not compact:
        return ""
    candidate = Path(compact)
    if candidate.is_absolute():
        return candidate.name or compact
    # Windows-style absolute paths without Path recognizing them on POSIX.
    if len(compact) >= 3 and compact[1] == ":" and compact[2] in {"\\", "/"}:
        return Path(compact.replace("\\", "/")).name or compact
    if compact.startswith("\\\\"):
        return Path(compact.replace("\\", "/")).name or compact
    return compact


def schema_versions(assessment: ModernizationAssessmentResult) -> dict[str, str]:
    """Return schema/agent versions for the report header."""

    return {
        "context_schema_version": LLM_CONTRACT_SCHEMA_VERSION,
        "recommendation_schema_version": AI_RECOMMENDATION_SCHEMA_VERSION,
        "agent_version": assessment.trace.agent_version or AGENT_VERSION,
        "agent_name": assessment.trace.agent_name,
    }


def _assert_recommendation_finding_links(
    recommendation_result: AIRecommendationResult,
    available_finding_ids: set[str],
) -> None:
    missing: set[str] = set()
    for recommendation in recommendation_result.recommendations:
        for finding_id in recommendation.related_finding_ids:
            if finding_id not in available_finding_ids:
                missing.add(finding_id)
    if missing:
        raise ModernizationReportValidationError(
            "Recommendation finding references do not resolve: " + ", ".join(sorted(missing))
        )


def _assert_phase_recommendation_links(
    recommendation_result: AIRecommendationResult,
) -> None:
    known = {item.recommendation_id for item in recommendation_result.recommendations}
    missing: set[str] = set()
    for phase in recommendation_result.modernization_phases:
        for recommendation_id in phase.recommendations:
            if recommendation_id not in known:
                missing.add(recommendation_id)
    if missing:
        raise ModernizationReportValidationError(
            "Phase recommendation references do not resolve: " + ", ".join(sorted(missing))
        )


def _slug(value: str) -> str:
    cleaned = []
    for char in value.strip():
        if char.isalnum() or char in {"-", "_"}:
            cleaned.append(char.lower())
        else:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    return slug or "item"


def analysis_finding_count(analysis_result: AnalysisResult) -> int:
    return len(analysis_result.findings)


def context_finding_count(analysis_context: LLMAnalysisContext) -> int:
    return len(analysis_context.findings)
