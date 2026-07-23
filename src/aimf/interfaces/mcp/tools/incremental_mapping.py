"""DTO mapping for incremental MCP tools."""

from __future__ import annotations

from typing import Any

from aimf.application.incremental.errors import IncrementalExecutionError
from aimf.application.incremental.execution_record import IncrementalExecutionRecord
from aimf.application.incremental.explainability import IncrementalExplanation
from aimf.application.incremental.models import IncrementalAssessmentPlan


def map_plan(plan: IncrementalAssessmentPlan) -> dict[str, Any]:
    return plan.model_dump(mode="json")


def map_execution_record(record: IncrementalExecutionRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")


def map_explanations(
    explanations: tuple[IncrementalExplanation, ...],
) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in explanations]


def map_incremental_error(error: BaseException) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": True,
        "message": str(error),
        "reason_code": getattr(error, "reason_code", "incremental_error"),
    }
    if isinstance(error, IncrementalExecutionError):
        if error.execution_id:
            payload["execution_id"] = error.execution_id
        if error.plan_id:
            payload["plan_id"] = error.plan_id
        if error.failed_step:
            payload["failed_step"] = error.failed_step
    return payload
