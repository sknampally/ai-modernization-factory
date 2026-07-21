"""Cross-contract validation for AI recommendation results."""

from __future__ import annotations

from aimf.ai.contracts.models import LLMAnalysisContext
from aimf.ai.recommendations.models import AIRecommendationResult


class AIRecommendationValidationError(ValueError):
    """Raised when an AI recommendation contract fails validation."""


def finding_ids_from_context(context: LLMAnalysisContext) -> set[str]:
    """Return finding identifiers available for recommendation references.

    The LLM evidence contract identifies findings primarily by ``rule_id``.
    """

    return {
        finding.rule_id
        for finding in context.findings
        if finding.rule_id and finding.rule_id.strip()
    }


def validate_recommendation_result(
    result: AIRecommendationResult,
    analysis_context: LLMAnalysisContext,
) -> AIRecommendationResult:
    """Validate recommendation references against an LLMAnalysisContext.

    Returns the same result when validation succeeds.
    """

    available_finding_ids = finding_ids_from_context(analysis_context)
    recommendation_ids = {item.recommendation_id for item in result.recommendations}

    unknown_finding_ids: set[str] = set()
    for recommendation in result.recommendations:
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
