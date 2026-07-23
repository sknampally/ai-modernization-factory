"""Persist Recommendation Engine artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aimf.domain.recommendations import RecommendationResult

RECOMMENDATIONS_FILENAME = "recommendations.json"


class RecommendationsArtifactWriteResult(BaseModel):
    """Result of writing recommendations.json."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    recommendation_count: int = Field(ge=0)
    providers_evaluated_count: int = Field(ge=0)


def write_recommendations_artifact(
    result: RecommendationResult,
    run_directory: Path,
) -> RecommendationsArtifactWriteResult:
    """Write deterministic recommendations.json under the assessment run directory."""

    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / RECOMMENDATIONS_FILENAME
    payload: dict[str, Any] = {
        "providers_evaluated": list(result.providers_evaluated),
        "providers_skipped": list(result.providers_skipped),
        "recommendation_count": result.recommendation_count,
        "recommendations": [item.model_dump(mode="json") for item in result.recommendations],
        "unmatched_finding_ids": list(result.unmatched_finding_ids),
        "version": result.version,
    }
    text = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    path.write_text(text + "\n", encoding="utf-8")
    return RecommendationsArtifactWriteResult(
        path=path,
        recommendation_count=result.recommendation_count,
        providers_evaluated_count=len(result.providers_evaluated),
    )


def format_recommendation_console_summary(result: RecommendationResult) -> tuple[str, ...]:
    """Return concise console lines for recommendation evaluation."""

    return (f"Recommendations: {result.recommendation_count}",)
