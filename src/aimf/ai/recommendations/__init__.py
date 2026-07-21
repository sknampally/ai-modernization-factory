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
    finding_ids_from_context,
    validate_recommendation_result,
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
    "ai_recommendation_result_from_json",
    "ai_recommendation_result_to_dict",
    "ai_recommendation_result_to_json",
    "finding_ids_from_context",
    "validate_recommendation_result",
]
