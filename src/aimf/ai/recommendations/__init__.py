"""Provider-neutral AI recommendation contracts."""

from aimf.ai.recommendations.enums import (
    AIRecommendationConfidence,
    AIRecommendationEffort,
    AIRecommendationImpact,
    AIRecommendationPriority,
)
from aimf.ai.recommendations.models import (
    AI_RECOMMENDATION_SCHEMA_VERSION,
    AIRecommendation,
    AIRecommendationResult,
    EvidenceCoverage,
    ModernizationPhase,
)
from aimf.ai.recommendations.serialization import (
    ai_recommendation_result_from_json,
    ai_recommendation_result_to_dict,
    ai_recommendation_result_to_json,
)
from aimf.ai.recommendations.validation import (
    AIRecommendationValidationError,
    RecommendationValidationOutcome,
    compute_evidence_coverage,
    deterministic_recommendation_ids_from_context,
    finding_ids_from_context,
    normalize_related_deterministic_recommendation_ids,
    validate_recommendation_result,
    validate_recommendation_result_outcome,
)

__all__ = [
    "AI_RECOMMENDATION_SCHEMA_VERSION",
    "AIRecommendation",
    "AIRecommendationConfidence",
    "AIRecommendationEffort",
    "AIRecommendationImpact",
    "AIRecommendationPriority",
    "AIRecommendationResult",
    "AIRecommendationValidationError",
    "EvidenceCoverage",
    "ModernizationPhase",
    "RecommendationValidationOutcome",
    "ai_recommendation_result_from_json",
    "ai_recommendation_result_to_dict",
    "ai_recommendation_result_to_json",
    "compute_evidence_coverage",
    "deterministic_recommendation_ids_from_context",
    "finding_ids_from_context",
    "normalize_related_deterministic_recommendation_ids",
    "validate_recommendation_result",
    "validate_recommendation_result_outcome",
]
