"""Cross-contract validation for AI recommendation results."""

from __future__ import annotations

import re
from pathlib import Path

from aimf.ai.contracts.models import LLMAnalysisContext, LLMFindingEvidence
from aimf.ai.recommendations.enums import AIRecommendationPriority
from aimf.ai.recommendations.models import AIRecommendation, AIRecommendationResult

_SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

_PRIORITY_RANK = {
    AIRecommendationPriority.LOW: 1,
    AIRecommendationPriority.MEDIUM: 2,
    AIRecommendationPriority.HIGH: 3,
    AIRecommendationPriority.CRITICAL: 4,
}

_PATH_LIKE = re.compile(
    r"(?P<path>(?:[A-Za-z]:\\|/Users/|/home/|/tmp/|/var/|/private/|"
    r"(?:[\w.-]+/)+\w[\w.-]*\.\w{1,8}))"
)


class AIRecommendationValidationError(ValueError):
    """Raised when an AI recommendation contract fails validation."""


def finding_ids_from_context(context: LLMAnalysisContext) -> set[str]:
    """Return finding identifiers available for recommendation references.

    Accepts rule IDs, group IDs, and stable finding IDs from the LLM context.
    """

    available: set[str] = set()
    for finding in context.findings:
        for candidate in (
            finding.rule_id,
            finding.group_id,
            finding.finding_id,
        ):
            if candidate and candidate.strip():
                available.add(candidate.strip())
    for recommendation in context.deterministic_recommendations:
        if recommendation.recommendation_id.strip():
            available.add(recommendation.recommendation_id.strip())
    return available


def validate_recommendation_result(
    result: AIRecommendationResult,
    analysis_context: LLMAnalysisContext,
) -> AIRecommendationResult:
    """Validate recommendation references against an LLMAnalysisContext.

    Returns the same result when validation succeeds.
    """

    available_finding_ids = finding_ids_from_context(analysis_context)
    recommendation_ids = {item.recommendation_id for item in result.recommendations}
    findings_by_id = _findings_by_id(analysis_context)
    evidence_paths = _evidence_paths(analysis_context)

    if len(result.key_risks) > 5:
        raise AIRecommendationValidationError("key_risks must contain at most 5 items")
    if not (5 <= len(result.recommendations) <= 8):
        # Allow fewer when the evidence set is tiny (tests / sparse repos).
        available_findings = len(analysis_context.findings)
        if available_findings >= 8 and not (5 <= len(result.recommendations) <= 8):
            raise AIRecommendationValidationError(
                "recommendations must contain between 5 and 8 items for evidence-rich assessments"
            )
        if available_findings < 8 and len(result.recommendations) > 8:
            raise AIRecommendationValidationError("recommendations must contain at most 8 items")
    if not (3 <= len(result.modernization_phases) <= 4):
        available_findings = len(analysis_context.findings)
        if available_findings >= 8 and not (3 <= len(result.modernization_phases) <= 4):
            raise AIRecommendationValidationError("modernization_phases must contain 3 or 4 phases")

    unknown_finding_ids: set[str] = set()
    for recommendation in result.recommendations:
        if not recommendation.related_finding_ids:
            raise AIRecommendationValidationError(
                f"recommendation {recommendation.recommendation_id} requires "
                "related_finding_ids evidence references"
            )
        for finding_id in recommendation.related_finding_ids:
            if finding_id not in available_finding_ids:
                unknown_finding_ids.add(finding_id)

        unknown_dependencies = sorted(set(recommendation.dependencies) - recommendation_ids)
        if unknown_dependencies:
            raise AIRecommendationValidationError(
                "recommendation dependencies reference unknown recommendation IDs: "
                + ", ".join(unknown_dependencies)
            )

    if unknown_finding_ids:
        raise AIRecommendationValidationError(
            "related_finding_ids reference findings not present in "
            "LLMAnalysisContext: " + ", ".join(sorted(unknown_finding_ids))
        )

    for recommendation in result.recommendations:
        _validate_severity_escalation(recommendation, findings_by_id)
        _validate_no_invented_paths(recommendation, evidence_paths)

    available_count = len(analysis_context.findings)
    if result.evidence_coverage.input_truncated:
        max_considered = max(
            available_count,
            analysis_context.findings_truncation.original_count,
        )
    else:
        max_considered = available_count

    if result.evidence_coverage.findings_considered > max_considered:
        raise AIRecommendationValidationError(
            "findings_considered exceeds findings available in LLMAnalysisContext"
        )

    return result


def _findings_by_id(context: LLMAnalysisContext) -> dict[str, LLMFindingEvidence]:
    indexed: dict[str, LLMFindingEvidence] = {}
    for finding in context.findings:
        for key in (finding.rule_id, finding.group_id, finding.finding_id):
            if key and key.strip() and key.strip() not in indexed:
                indexed[key.strip()] = finding
    return indexed


def _evidence_paths(context: LLMAnalysisContext) -> set[str]:
    paths: set[str] = set()
    for finding in context.findings:
        for evidence in finding.evidence:
            compact = evidence.path.strip().replace("\\", "/")
            if compact:
                paths.add(compact)
                paths.add(Path(compact).name)
    return paths


def _validate_severity_escalation(
    recommendation: AIRecommendation,
    findings_by_id: dict[str, LLMFindingEvidence],
) -> None:
    priority_rank = _PRIORITY_RANK.get(recommendation.priority, 0)
    if priority_rank < _PRIORITY_RANK[AIRecommendationPriority.HIGH]:
        return
    related = [
        findings_by_id[finding_id]
        for finding_id in recommendation.related_finding_ids
        if finding_id in findings_by_id
    ]
    if not related:
        raise AIRecommendationValidationError(
            f"recommendation {recommendation.recommendation_id} has no grounded "
            "finding evidence for its priority"
        )
    max_evidence = max(_SEVERITY_RANK.get(item.severity.lower(), 0) for item in related)
    # Critical AI priority requires at least one high/critical finding.
    if (
        recommendation.priority == AIRecommendationPriority.CRITICAL
        and max_evidence < _SEVERITY_RANK["high"]
    ):
        raise AIRecommendationValidationError(
            f"recommendation {recommendation.recommendation_id} escalates severity "
            "to critical without high/critical supporting evidence"
        )
    # High AI priority requires at least medium evidence.
    if (
        recommendation.priority == AIRecommendationPriority.HIGH
        and max_evidence < _SEVERITY_RANK["medium"]
    ):
        raise AIRecommendationValidationError(
            f"recommendation {recommendation.recommendation_id} escalates severity "
            "to high without medium+ supporting evidence"
        )


def _validate_no_invented_paths(
    recommendation: AIRecommendation,
    evidence_paths: set[str],
) -> None:
    blobs = [
        recommendation.description,
        recommendation.rationale,
        *recommendation.suggested_actions,
    ]
    for blob in blobs:
        for match in _PATH_LIKE.finditer(blob):
            candidate = match.group("path").strip().replace("\\", "/")
            if candidate.startswith(("/", "\\")) or (
                len(candidate) >= 3 and candidate[1] == ":" and candidate[2] in {"\\", "/"}
            ):
                raise AIRecommendationValidationError(
                    f"recommendation {recommendation.recommendation_id} references "
                    "an absolute path not present in evidence"
                )
            if candidate not in evidence_paths and Path(candidate).name not in evidence_paths:
                # Allow generic non-repo path-like tokens only when clearly relative
                # and matching evidence; otherwise reject invented repo paths.
                if "/" in candidate or "\\" in candidate:
                    raise AIRecommendationValidationError(
                        f"recommendation {recommendation.recommendation_id} references "
                        f"path '{candidate}' not present in evidence"
                    )
