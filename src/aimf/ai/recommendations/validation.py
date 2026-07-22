"""Cross-contract validation for AI recommendation results."""

from __future__ import annotations

import re
from pathlib import Path

from aimf.ai.contracts.models import LLMAnalysisContext, LLMFindingEvidence
from aimf.ai.recommendations.enums import AIRecommendationPriority
from aimf.ai.recommendations.models import (
    AI_RECOMMENDATION_ID_PATTERN,
    AIRecommendation,
    AIRecommendationResult,
    EvidenceCoverage,
)

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

    def __init__(self, message: str, *, issues: list[str] | None = None) -> None:
        self.issues = list(issues) if issues is not None else [message]
        super().__init__(message if issues is None else "; ".join(self.issues))


def finding_ids_from_context(context: LLMAnalysisContext) -> set[str]:
    """Return finding identifiers available for related_finding_ids.

    Accepts rule IDs, group IDs, and stable finding IDs from the LLM context.
    Deterministic recommendation IDs are intentionally excluded.
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
    return available


def deterministic_recommendation_ids_from_context(context: LLMAnalysisContext) -> set[str]:
    """Return deterministic recommendation IDs available for AI traceability."""

    available: set[str] = set()
    for recommendation in context.deterministic_recommendations:
        compact = recommendation.recommendation_id.strip()
        if compact:
            available.add(compact)
    return available


def compute_evidence_coverage(
    result: AIRecommendationResult,
    analysis_context: LLMAnalysisContext,
) -> EvidenceCoverage:
    """Compute authoritative coverage from unique valid related_finding_ids."""

    available_finding_ids = finding_ids_from_context(analysis_context)
    referenced: set[str] = set()
    for recommendation in result.recommendations:
        for finding_id in recommendation.related_finding_ids:
            if finding_id in available_finding_ids:
                referenced.add(finding_id)

    included = analysis_context.findings_truncation.included_count
    total = max(
        analysis_context.findings_truncation.original_count,
        included,
        len(analysis_context.findings),
    )
    referenced_count = len(referenced)
    if included == 0:
        percentage = 0.0
    else:
        percentage = round(100.0 * referenced_count / included, 2)

    truncated = bool(analysis_context.findings_truncation.truncated)
    return EvidenceCoverage(
        total_findings=total,
        findings_considered=included,
        findings_referenced=referenced_count,
        coverage_percentage=percentage,
        input_truncated=truncated,
    )


def validate_recommendation_result(
    result: AIRecommendationResult,
    analysis_context: LLMAnalysisContext,
) -> AIRecommendationResult:
    """Validate recommendation references against an LLMAnalysisContext.

    Returns a result with deterministically recomputed evidence_coverage when
    validation succeeds. Aggregates independent contract issues when practical.
    """

    issues: list[str] = []
    available_finding_ids = finding_ids_from_context(analysis_context)
    available_deterministic_ids = deterministic_recommendation_ids_from_context(analysis_context)
    recommendation_ids = {item.recommendation_id for item in result.recommendations}
    findings_by_id = _findings_by_id(analysis_context)
    evidence_paths = _evidence_paths(analysis_context)
    available_findings = len(analysis_context.findings)
    evidence_rich = available_findings >= 8

    if len(result.key_risks) > 5:
        issues.append("key_risks must contain at most 5 items")

    recommendation_count = len(result.recommendations)
    if evidence_rich and not (5 <= recommendation_count <= 8):
        issues.append(
            "recommendations must contain between 5 and 8 items for evidence-rich assessments"
        )
    elif recommendation_count > 8:
        issues.append("recommendations must contain at most 8 items")

    for recommendation in result.recommendations:
        if not AI_RECOMMENDATION_ID_PATTERN.fullmatch(recommendation.recommendation_id):
            issues.append(
                f"recommendation_id '{recommendation.recommendation_id}' must match AI-REC-NNN"
            )

    if evidence_rich and not (2 <= len(result.modernization_phases) <= 4):
        issues.append("modernization_phases must contain 2 to 4 phases")
    elif len(result.modernization_phases) > 4:
        issues.append("modernization_phases must contain at most 4 phases")

    for phase in result.modernization_phases:
        if not phase.recommendations:
            issues.append(f"modernization phase {phase.phase} must not be empty")

    if result.modernization_phases:
        assigned: list[str] = []
        for phase in result.modernization_phases:
            unknown = sorted(set(phase.recommendations) - recommendation_ids)
            if unknown:
                issues.append(
                    "modernization phases reference unknown recommendation IDs: "
                    + ", ".join(unknown)
                )
            assigned.extend(phase.recommendations)
        if len(assigned) != len(set(assigned)):
            issues.append("each AI recommendation may appear in at most one modernization phase")
        missing = sorted(recommendation_ids - set(assigned))
        if missing:
            issues.append("modernization phases omit recommendation IDs: " + ", ".join(missing))

    unknown_finding_ids: set[str] = set()
    unknown_deterministic_ids: set[str] = set()
    for recommendation in result.recommendations:
        if not recommendation.related_finding_ids:
            issues.append(
                f"recommendation {recommendation.recommendation_id} requires "
                "related_finding_ids evidence references"
            )
        for finding_id in recommendation.related_finding_ids:
            det_as_finding = (
                finding_id in available_deterministic_ids
                and finding_id not in available_finding_ids
            )
            if det_as_finding:
                issues.append(
                    f"recommendation {recommendation.recommendation_id} places "
                    f"deterministic recommendation ID '{finding_id}' in "
                    "related_finding_ids; use related_deterministic_recommendation_ids"
                )
            elif finding_id not in available_finding_ids:
                unknown_finding_ids.add(finding_id)

        for det_id in recommendation.related_deterministic_recommendation_ids:
            if det_id not in available_deterministic_ids:
                unknown_deterministic_ids.add(det_id)

        unknown_dependencies = sorted(set(recommendation.dependencies) - recommendation_ids)
        if unknown_dependencies:
            issues.append(
                "recommendation dependencies reference unknown recommendation IDs: "
                + ", ".join(unknown_dependencies)
            )

        try:
            _validate_severity_escalation(recommendation, findings_by_id)
        except AIRecommendationValidationError as error:
            issues.extend(error.issues)

        try:
            _validate_no_invented_paths(recommendation, evidence_paths)
        except AIRecommendationValidationError as error:
            issues.extend(error.issues)

    if unknown_finding_ids:
        issues.append(
            "related_finding_ids reference findings not present in "
            "LLMAnalysisContext: " + ", ".join(sorted(unknown_finding_ids))
        )
    if unknown_deterministic_ids:
        issues.append(
            "related_deterministic_recommendation_ids reference IDs not present in "
            "LLMAnalysisContext: " + ", ".join(sorted(unknown_deterministic_ids))
        )

    computed_coverage = compute_evidence_coverage(result, analysis_context)
    if result.evidence_coverage.findings_considered > computed_coverage.total_findings:
        issues.append("findings_considered exceeds findings available in LLMAnalysisContext")

    if issues:
        raise AIRecommendationValidationError("; ".join(issues), issues=issues)

    return result.model_copy(update={"evidence_coverage": computed_coverage})


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
