"""Developer diagnostic artifact for rejected AI model responses."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from aimf.reporting.modernization_models import AIAttemptInfo, AIExecutionStatus

AI_RESPONSE_DIAGNOSTIC_FILENAME = "ai-response-diagnostic.json"
AI_RESPONSE_DIAGNOSTIC_SCHEMA_VERSION = "1.0"

_CREDENTIAL_KEY_FRAGMENTS = (
    "credential",
    "secret",
    "password",
    "token",
    "authorization",
    "auth_header",
    "access_key",
    "session_token",
    "aws_access",
    "aws_secret",
    "sso",
)


def build_ai_response_diagnostic(
    *,
    status: AIExecutionStatus,
    attempt: AIAttemptInfo | None,
    raw_model_text: str | None,
    parsed_json: dict[str, Any] | None,
    validation_error_summary: str | None,
    validation_diagnostics: str | None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build a developer-facing diagnostic document for a rejected AI response."""

    moment = timestamp if timestamp is not None else datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    else:
        moment = moment.astimezone(UTC)

    usage = None
    if attempt is not None and any(
        value is not None
        for value in (attempt.input_tokens, attempt.output_tokens, attempt.total_tokens)
    ):
        usage = {
            "input_tokens": attempt.input_tokens,
            "output_tokens": attempt.output_tokens,
            "total_tokens": attempt.total_tokens,
        }

    document: dict[str, Any] = {
        "schema_version": AI_RESPONSE_DIAGNOSTIC_SCHEMA_VERSION,
        "artifact": "ai-response-diagnostic",
        "timestamp_utc": moment.isoformat().replace("+00:00", "Z"),
        "provider": attempt.provider if attempt is not None else None,
        "model_id": attempt.model_id if attempt is not None else None,
        "execution_status": status.value,
        "stages_completed": (
            [stage.value for stage in attempt.stages_completed] if attempt is not None else []
        ),
        "usage": usage,
        "latency_ms": attempt.latency_ms if attempt is not None else None,
        "stop_reason": attempt.stop_reason if attempt is not None else None,
        "failure_code": attempt.failure_code if attempt is not None else None,
        "validation_error_summary": validation_error_summary,
        "validation_diagnostics": validation_diagnostics,
        "raw_model_text": raw_model_text,
        "parsed_json": parsed_json,
    }
    return cast(dict[str, Any], _strip_credential_fields(document))


def write_ai_response_diagnostic(run_directory: Path, document: dict[str, Any]) -> Path:
    """Write ``ai-response-diagnostic.json`` under the assessment run directory."""

    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / AI_RESPONSE_DIAGNOSTIC_FILENAME
    sanitized = _strip_credential_fields(document)
    text = json.dumps(
        sanitized,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ": "),
    )
    if not text.endswith("\n"):
        text += "\n"
    # Text-only JSON; never treat contents as HTML/JS.
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _strip_credential_fields(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in _CREDENTIAL_KEY_FRAGMENTS):
                continue
            cleaned[key] = _strip_credential_fields(item)
        return cleaned
    if isinstance(value, list):
        return [_strip_credential_fields(item) for item in value]
    return value
