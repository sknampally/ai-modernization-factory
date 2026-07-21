"""Serialization and file output helpers for modernization HTML reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aimf.reporting.modernization_html import ModernizationHTMLReportRenderer
from aimf.reporting.modernization_models import ModernizationReportInput


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise TypeError("Naive datetime is not supported")
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def modernization_report_input_to_dict(
    report_input: ModernizationReportInput,
) -> dict[str, Any]:
    """Return a deterministic JSON-ready dictionary."""

    return report_input.model_dump(mode="json")


def modernization_report_input_to_json(
    report_input: ModernizationReportInput,
    *,
    indent: int | None = 2,
) -> str:
    """Serialize ModernizationReportInput to stable JSON text."""

    payload = modernization_report_input_to_dict(report_input)
    return json.dumps(
        payload,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        default=_json_default,
        separators=(",", ": ") if indent is not None else (",", ":"),
    )


def modernization_report_input_from_json(
    payload: str | bytes | dict[str, Any],
) -> ModernizationReportInput:
    """Validate JSON (or a dict) against ModernizationReportInput."""

    if isinstance(payload, dict):
        data = payload
    else:
        data = json.loads(payload)
    return ModernizationReportInput.model_validate(data)


def write_modernization_html_report(
    report_input: ModernizationReportInput,
    output_path: Path | str,
) -> Path:
    """Render and write a UTF-8 HTML modernization assessment report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = ModernizationHTMLReportRenderer().render(report_input)
    path.write_text(html, encoding="utf-8")
    return path
