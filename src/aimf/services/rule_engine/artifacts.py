"""Persist Rule Engine findings artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aimf.domain.findings import RuleEvaluationResult

FINDINGS_FILENAME = "findings.json"


class FindingsArtifactWriteResult(BaseModel):
    """Result of writing findings.json."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: Path
    finding_count: int = Field(ge=0)
    rules_evaluated_count: int = Field(ge=0)


def write_findings_artifact(
    evaluation: RuleEvaluationResult,
    run_directory: Path,
) -> FindingsArtifactWriteResult:
    """Write deterministic findings.json under the assessment run directory."""

    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / FINDINGS_FILENAME
    payload: dict[str, Any] = {
        "finding_count": evaluation.finding_count,
        "findings": [item.model_dump(mode="json") for item in evaluation.findings],
        "rules_evaluated": list(evaluation.rules_evaluated),
        "rules_skipped": list(evaluation.rules_skipped),
    }
    text = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    path.write_text(text + "\n", encoding="utf-8")
    return FindingsArtifactWriteResult(
        path=path,
        finding_count=evaluation.finding_count,
        rules_evaluated_count=len(evaluation.rules_evaluated),
    )


def format_rule_console_summary(
    evaluation: RuleEvaluationResult,
    *,
    recommendation_count: int | None = None,
) -> tuple[str, ...]:
    """Return concise console lines for rule evaluation (and recommendations)."""

    lines: list[str] = [
        f"Rules Evaluated: {len(evaluation.rules_evaluated)}",
        f"Findings: {evaluation.finding_count}",
    ]
    if recommendation_count is not None:
        lines.append(f"Recommendations: {recommendation_count}")
    return tuple(lines)
