"""Sanitized machine-readable assessment JSON artifact."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from typing import Any

from aimf.models import AnalysisResult, Finding, Priority, Recommendation, Severity, Technology
from aimf.reporting.ai_execution import AI_EXECUTION_FILENAME
from aimf.reporting.modernization_models import (
    AIExecutionStatus,
    AssessmentTiming,
    ModernizationReportInput,
)
from aimf.reporting.modernization_view import (
    repository_identifier,
    sanitize_display_path,
    sorted_findings,
)
from aimf.static_analysis.models import StaticAnalysisResult, StaticAnalysisStatus

ASSESSMENT_JSON_SCHEMA_VERSION = "1.2"
ASSESSMENT_JSON_REPORT_VERSION = "1.2"


def build_assessment_json_document(
    report_input: ModernizationReportInput,
) -> dict[str, Any]:
    """Build a sanitized, customer-safe assessment JSON document."""

    analysis = report_input.analysis_result
    ai_block = _ai_block(report_input)
    static_analysis = _static_analysis_block(analysis.static_analysis_results)
    timing = _timing_block(report_input.timing)
    repository_reference = report_input.repository_reference or repository_identifier(report_input)
    executive = _executive_summary_metrics(analysis)
    comparison = _comparison_payload(analysis)

    assessment: dict[str, Any] = {
            "mode": report_input.assessment_mode.value,
            "generated_at": _format_timestamp(report_input.generated_at_utc),
            "report_title": report_input.report_title,
            "organization_name": report_input.organization_name,
            "repository": {
                "name": analysis.repository.name,
                "reference": repository_reference,
                "source_type": ("github" if analysis.repository.source_url else "local"),
                "default_branch": analysis.repository.default_branch,
                "file_count": analysis.repository.total_files or len(analysis.repository.files),
            },
            "summary": {
                "technology_count": len(analysis.technologies),
                "finding_count": len(analysis.findings),
                "deterministic_recommendation_count": len(analysis.recommendations),
                "recommendation_count": len(analysis.recommendations),
                "ai_recommendation_count": ai_block["recommendation_count"],
                "phase_count": ai_block["phase_count"],
                "ai_executed": report_input.ai_executed,
                "static_analysis_status": static_analysis["status"],
                "findings_by_severity": executive["findings_by_severity"],
                "recommendations_by_priority": executive["recommendations_by_priority"],
                "critical_high_finding_count": executive["critical_high_finding_count"],
                "tests_detected": executive["tests_detected"],
                "ci_detected": executive["ci_detected"],
                "cloud_capabilities": executive["cloud_capabilities"],
                "summary_text": executive["summary_text"],
            },
            "executive_summary": executive,
            "technologies": [
                _technology_payload(item)
                for item in sorted(
                    analysis.technologies,
                    key=lambda tech: (
                        str(getattr(tech.category, "value", tech.category)).lower(),
                        tech.name.lower(),
                    ),
                )
            ],
            "repository_facts": _facts_payload(analysis),
            "findings": [_finding_payload(item) for item in sorted_findings(analysis.findings)],
            "deterministic_recommendations": [
                _recommendation_payload(item) for item in analysis.recommendations
            ],
            "comparison": comparison,
            "warnings": list(report_input.warnings),
            "static_analysis": static_analysis,
            "ai": {
                "executed": report_input.ai_executed,
                "status": ai_block.get("status"),
                "result_included": ai_block.get("result_included"),
                "provider_invoked": ai_block.get("provider_invoked"),
                "fallback_used": ai_block.get("fallback_used"),
                "stages_completed": ai_block.get("stages_completed"),
                "model_id": ai_block["model_id"],
                "provider": ai_block["provider"],
                "input_tokens": ai_block["input_tokens"],
                "output_tokens": ai_block["output_tokens"],
                "total_tokens": ai_block["total_tokens"],
                "latency_ms": ai_block["latency_ms"],
                "stop_reason": ai_block.get("stop_reason"),
                "executive_summary": ai_block["executive_summary"],
                "overall_assessment": ai_block["overall_assessment"],
                "key_risks": ai_block["key_risks"],
                "recommendations": ai_block["recommendations"],
                "phases": ai_block["phases"],
                "limitations": ai_block["limitations"],
                "evidence_coverage": ai_block["evidence_coverage"],
                "candidate_finding_count": ai_block.get("candidate_finding_count"),
                "included_finding_count": ai_block.get("included_finding_count"),
                "omitted_informational_count": ai_block.get("omitted_informational_count"),
                "static_analysis_profile": ai_block.get("static_analysis_profile"),
                "estimated_input_tokens": ai_block.get("estimated_input_tokens"),
                "failure_code": ai_block.get("failure_code"),
                "failure_message": ai_block.get("failure_message"),
                "failure_detail": ai_block.get("failure_detail"),
                "internal_execution_artifact": ai_block.get("internal_execution_artifact"),
            },
            "timing": timing,
            "coverage": {
                "deterministic_analysis": "completed",
                "static_analysis": static_analysis["status"],
                "ai_interpretation": ai_block.get("status")
                or AIExecutionStatus.NOT_REQUESTED.value,
            },
        }
    # Optional Phase 4.2.5 architecture report section (schema remains 1.2; additive key).
    if report_input.architecture_report is not None:
        assessment["architecture"] = report_input.architecture_report.model_dump(
            mode="json"
        )
    return {
        "schema_version": ASSESSMENT_JSON_SCHEMA_VERSION,
        "report_version": ASSESSMENT_JSON_REPORT_VERSION,
        "assessment": assessment,
    }

def assessment_json_to_text(document: dict[str, Any], *, indent: int | None = 2) -> str:
    """Serialize an assessment JSON document with stable formatting."""

    text = json.dumps(
        document,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ": ") if indent is not None else (",", ":"),
    )
    return text if text.endswith("\n") else f"{text}\n"


def _executive_summary_metrics(analysis: AnalysisResult) -> dict[str, Any]:
    severity_counts = Counter(
        str(getattr(finding.severity, "value", finding.severity)).lower()
        for finding in analysis.findings
    )
    priority_counts = Counter(
        str(getattr(item.priority, "value", item.priority)).lower()
        for item in analysis.recommendations
    )
    structure = analysis.facts.structure
    cicd = analysis.facts.cicd
    cloud = analysis.facts.cloud
    critical_high = sum(
        1 for finding in analysis.findings if finding.severity in {Severity.CRITICAL, Severity.HIGH}
    )
    tests_detected = structure.has_tests if structure is not None else None
    ci_detected = cicd.has_ci if cicd is not None else None
    cloud_capabilities = list(cloud.cloud_capabilities) if cloud is not None else []

    finding_count = len(analysis.findings)
    recommendation_count = len(analysis.recommendations)
    critical_findings = sum(finding.severity == Severity.CRITICAL for finding in analysis.findings)
    high_recommendations = sum(
        item.priority in {Priority.CRITICAL, Priority.HIGH} for item in analysis.recommendations
    )
    parts = [
        (
            f"Analyzed repository '{analysis.repository.name}' with "
            f"{len(analysis.repository.files)} scanned file(s)."
        ),
        (
            f"Detected {finding_count} finding(s) "
            f"({critical_findings} critical) and "
            f"{recommendation_count} recommendation(s) "
            f"({high_recommendations} critical/high priority)."
        ),
    ]
    if tests_detected is not None:
        parts.append(
            "Automated tests were detected."
            if tests_detected
            else "No automated tests were detected."
        )
    if ci_detected is not None:
        parts.append("CI was detected." if ci_detected else "No CI pipeline was detected.")
    if cloud_capabilities:
        parts.append("Cloud capabilities detected: " + ", ".join(cloud_capabilities) + ".")

    return {
        "summary_text": " ".join(parts),
        "finding_count": finding_count,
        "recommendation_count": recommendation_count,
        "file_count": analysis.repository.total_files or len(analysis.repository.files),
        "technology_count": len(analysis.technologies),
        "findings_by_severity": {
            key: severity_counts.get(key, 0)
            for key in ("critical", "high", "medium", "low", "info")
        },
        "recommendations_by_priority": {
            key: priority_counts.get(key, 0) for key in ("critical", "high", "medium", "low")
        },
        "critical_high_finding_count": critical_high,
        "tests_detected": tests_detected,
        "ci_detected": ci_detected,
        "cloud_capabilities": cloud_capabilities,
    }


def _facts_payload(analysis: AnalysisResult) -> dict[str, Any]:
    facts = analysis.facts
    return {
        "structure": facts.structure.model_dump(mode="json") if facts.structure else None,
        "technology": facts.technology.model_dump(mode="json") if facts.technology else None,
        "build": facts.build.model_dump(mode="json") if facts.build else None,
        "dependencies": (
            facts.dependencies.model_dump(mode="json") if facts.dependencies else None
        ),
        "cicd": facts.cicd.model_dump(mode="json") if facts.cicd else None,
        "security": facts.security.model_dump(mode="json") if facts.security else None,
        "architecture": (
            facts.architecture.model_dump(mode="json") if facts.architecture else None
        ),
        "cloud": facts.cloud.model_dump(mode="json") if facts.cloud else None,
    }


def _comparison_payload(analysis: AnalysisResult) -> dict[str, Any] | None:
    comparison = analysis.comparison
    if comparison is None or not comparison.baseline_available:
        return None
    payload = comparison.model_dump(mode="json")
    sanitized = _sanitize_payload_paths(payload)
    assert isinstance(sanitized, dict)
    return sanitized


def _ai_block(report_input: ModernizationReportInput) -> dict[str, Any]:
    budget = None
    if (
        report_input.analysis_context is not None
        and report_input.analysis_context.budget is not None
    ):
        budget = report_input.analysis_context.budget.model_dump(mode="json")

    attempt = report_input.ai_attempt
    stages = [stage.value for stage in attempt.stages_completed] if attempt is not None else []
    budget_fields = {
        "candidate_finding_count": budget.get("candidate_finding_count") if budget else None,
        "included_finding_count": budget.get("included_finding_count") if budget else None,
        "omitted_informational_count": (
            budget.get("omitted_informational_count") if budget else None
        ),
        "static_analysis_profile": (budget.get("static_analysis_profile") if budget else None),
        "estimated_input_tokens": budget.get("estimated_input_tokens") if budget else None,
    }

    if report_input.ai_status != AIExecutionStatus.SUCCEEDED:
        latency_ms = None
        if attempt is not None and attempt.latency_ms is not None:
            latency_ms = attempt.latency_ms
        elif report_input.timing is not None:
            latency_ms = report_input.timing.ai_ms
        return {
            "status": report_input.ai_status.value,
            "executed": False,
            "result_included": False,
            "provider_invoked": report_input.ai_provider_invoked,
            "fallback_used": report_input.ai_fallback_used,
            "stages_completed": stages,
            "recommendation_count": 0,
            "phase_count": 0,
            "model_id": attempt.model_id if attempt is not None else None,
            "provider": attempt.provider if attempt is not None else None,
            "input_tokens": attempt.input_tokens if attempt is not None else None,
            "output_tokens": attempt.output_tokens if attempt is not None else None,
            "total_tokens": attempt.total_tokens if attempt is not None else None,
            "latency_ms": latency_ms,
            "stop_reason": attempt.stop_reason if attempt is not None else None,
            "executive_summary": None,
            "overall_assessment": None,
            "key_risks": [],
            "recommendations": [],
            "phases": [],
            "limitations": [],
            "evidence_coverage": None,
            "failure_code": (attempt.failure_code if attempt is not None else None),
            "failure_message": _sanitize_optional_message(report_input.ai_failure_message),
            "failure_detail": _sanitize_optional_message(
                attempt.failure_detail if attempt is not None else None
            ),
            "internal_execution_artifact": (
                AI_EXECUTION_FILENAME
                if report_input.ai_status != AIExecutionStatus.NOT_REQUESTED
                else None
            ),
            **budget_fields,
        }

    assessment = report_input.assessment_result
    assert assessment is not None
    recommendation = assessment.recommendation_result
    metadata = assessment.model_metadata
    usage = metadata.usage
    return {
        "status": AIExecutionStatus.SUCCEEDED.value,
        "executed": True,
        "result_included": True,
        "provider_invoked": True,
        "fallback_used": False,
        "stages_completed": stages
        or [
            "requested",
            "provider_invoked",
            "response_received",
            "response_parsed",
            "response_validated",
            "result_included",
        ],
        "recommendation_count": len(recommendation.recommendations),
        "phase_count": len(recommendation.modernization_phases),
        "model_id": metadata.model_id,
        "provider": metadata.provider,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "latency_ms": metadata.latency_ms,
        "stop_reason": metadata.stop_reason,
        "executive_summary": recommendation.executive_summary,
        "overall_assessment": recommendation.overall_assessment,
        "key_risks": list(recommendation.key_risks),
        "recommendations": [
            item.model_dump(mode="json") for item in recommendation.recommendations
        ],
        "phases": [item.model_dump(mode="json") for item in recommendation.modernization_phases],
        "limitations": list(recommendation.limitations),
        "evidence_coverage": recommendation.evidence_coverage.model_dump(mode="json"),
        "failure_code": None,
        "failure_message": None,
        "failure_detail": None,
        "internal_execution_artifact": AI_EXECUTION_FILENAME,
        **budget_fields,
    }


def _static_analysis_block(results: list[StaticAnalysisResult]) -> dict[str, Any]:
    if not results:
        return {
            "status": StaticAnalysisStatus.DISABLED.value,
            "providers": [],
            "provider": None,
            "provider_version": None,
            "finding_count": 0,
            "duration_ms": None,
            "message": "Static analysis was not configured for this assessment.",
            "profile": None,
            "rulesets": None,
            "eligible_file_count": 0,
            "files_analyzed": 0,
            "raw_observation_count": 0,
            "grouped_finding_count": 0,
            "primary_count": 0,
            "supporting_count": 0,
            "informational_count": 0,
            "suppressed_from_html_count": 0,
            "observations": [],
            "groups": [],
        }

    primary = results[0]
    providers = [
        {
            "provider_id": item.provider_id,
            "provider": item.provider_name,
            "status": item.status.value,
            "provider_version": item.provider_version,
            "finding_count": len(item.findings),
            "eligible_file_count": item.eligible_file_count,
            "files_analyzed": item.files_analyzed,
            "rulesets": item.command_metadata.get("rulesets"),
            "profile": item.profile or item.command_metadata.get("profile"),
            "duration_ms": item.duration_ms,
            "raw_observation_count": item.raw_observation_count,
            "grouped_finding_count": item.grouped_finding_count,
            "primary_count": item.primary_count,
            "supporting_count": item.supporting_count,
            "informational_count": item.informational_count,
            "suppressed_from_html_count": item.suppressed_from_html_count,
            "message": _sanitize_optional_message(item.error_message),
            "warnings": [
                _sanitize_optional_message(warning) or warning for warning in item.warnings
            ],
        }
        for item in results
    ]
    observations = [
        _observation_payload(observation) for item in results for observation in item.observations
    ]
    groups = [_group_payload(group) for item in results for group in item.groups]
    return {
        "status": primary.status.value,
        "providers": providers,
        "provider": primary.provider_name,
        "provider_version": primary.provider_version,
        "finding_count": sum(len(item.findings) for item in results),
        "duration_ms": primary.duration_ms,
        "message": _sanitize_optional_message(primary.error_message),
        "profile": primary.profile or primary.command_metadata.get("profile"),
        "rulesets": primary.command_metadata.get("rulesets"),
        "eligible_file_count": primary.eligible_file_count,
        "files_analyzed": primary.files_analyzed,
        "raw_observation_count": sum(item.raw_observation_count for item in results),
        "grouped_finding_count": sum(item.grouped_finding_count for item in results),
        "primary_count": sum(item.primary_count for item in results),
        "supporting_count": sum(item.supporting_count for item in results),
        "informational_count": sum(item.informational_count for item in results),
        "suppressed_from_html_count": sum(item.suppressed_from_html_count for item in results),
        "observations": observations,
        "groups": groups,
    }


def _observation_payload(observation: Any) -> dict[str, Any]:
    return {
        "observation_id": observation.observation_id,
        "provider": observation.provider_name,
        "provider_id": observation.provider_id,
        "rule_id": observation.rule_id,
        "external_rule_id": observation.external_rule_id,
        "provider_priority": observation.provider_priority,
        "provider_category": observation.provider_category,
        "normalized_category": observation.normalized_category.value,
        "normalized_severity": observation.normalized_severity.value,
        "customer_visibility": observation.customer_visibility.value,
        "modernization_relevance": observation.modernization_relevance.value,
        "file": sanitize_display_path(observation.file_path),
        "line": observation.line_number,
        "column": observation.column_number,
        "message": observation.message,
        "group_id": observation.group_id,
        "mapping_rationale": observation.mapping_rationale,
    }


def _group_payload(group: Any) -> dict[str, Any]:
    return {
        "group_id": group.group_id,
        "provider": group.provider_name,
        "provider_id": group.provider_id,
        "rule_id": group.rule_id,
        "title": group.title,
        "description": group.description,
        "category": group.category.value,
        "severity": group.severity.value,
        "customer_visibility": group.customer_visibility.value,
        "modernization_relevance": group.modernization_relevance.value,
        "occurrence_count": group.occurrence_count,
        "affected_file_count": group.affected_file_count,
        "representative_locations": [
            {
                "file_path": sanitize_display_path(str(location.get("file_path", ""))),
                "line_number": location.get("line_number"),
                "column_number": location.get("column_number"),
                "message": location.get("message"),
            }
            for location in group.representative_locations
        ],
        "observation_ids": list(group.observation_ids),
        "mapping_rationale": group.mapping_rationale,
    }


def _timing_block(timing: AssessmentTiming | None) -> dict[str, Any] | None:
    if timing is None:
        return None
    return {
        "total_ms": timing.total_ms,
        "scan_ms": timing.scan_ms,
        "analysis_ms": timing.analysis_ms,
        "static_analysis_ms": timing.static_analysis_ms,
        "ai_ms": timing.ai_ms,
        "report_ms": timing.report_ms,
    }


def _technology_payload(tech: Technology) -> dict[str, Any]:
    return {
        "name": tech.name,
        "category": str(getattr(tech.category, "value", tech.category)),
        "version": tech.version,
        "confidence": tech.confidence,
        "source": tech.source,
    }


def _finding_payload(finding: Finding) -> dict[str, Any]:
    return {
        "id": str(finding.id),
        "rule_id": finding.rule_id,
        "title": finding.title,
        "description": finding.description,
        "category": str(getattr(finding.category, "value", finding.category)),
        "severity": str(getattr(finding.severity, "value", finding.severity)),
        "source": str(getattr(finding.source, "value", finding.source)),
        "affected_technologies": list(finding.affected_technologies),
        "evidence": [
            {
                "file_path": sanitize_display_path(item.file_path),
                "line_number": item.line_number,
                "column_number": item.column_number,
                "description": item.description,
            }
            for item in finding.evidence
        ],
        "provider_name": finding.metadata.get("provider_name"),
        "customer_visibility": finding.metadata.get("customer_visibility"),
        "modernization_relevance": finding.metadata.get("modernization_relevance"),
        "group_id": finding.metadata.get("group_id"),
        "occurrence_count": finding.metadata.get("occurrence_count"),
        "affected_file_count": finding.metadata.get("affected_file_count"),
        "provider_priority": finding.metadata.get("original_priority"),
        "provider_category": finding.metadata.get("ruleset"),
    }


def _recommendation_payload(recommendation: Recommendation) -> dict[str, Any]:
    return {
        "id": str(recommendation.id),
        "rule_id": recommendation.rule_id,
        "title": recommendation.title,
        "description": recommendation.description,
        "rationale": recommendation.rationale,
        "priority": str(getattr(recommendation.priority, "value", recommendation.priority)),
        "category": str(getattr(recommendation.category, "value", recommendation.category)),
        "effort": str(getattr(recommendation.effort, "value", recommendation.effort)),
        "risk": str(getattr(recommendation.risk, "value", recommendation.risk)),
        "related_finding_ids": list(recommendation.related_finding_ids),
        "actions": list(recommendation.actions),
        "dependencies": list(recommendation.dependencies),
        "evidence": [
            {
                "file_path": sanitize_display_path(item.file_path),
                "line_number": item.line_number,
                "column_number": item.column_number,
                "description": item.description,
            }
            for item in recommendation.evidence
        ],
    }


def _sanitize_payload_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_payload_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload_paths(item) for item in value]
    if isinstance(value, str):
        if "/" in value or "\\" in value:
            candidate = sanitize_display_path(value)
            if candidate != value and (
                value.startswith("/") or (len(value) >= 3 and value[1] == ":")
            ):
                return candidate
            return _strip_absolute_paths(value)
        return value
    return value


def _sanitize_optional_message(message: str | None) -> str | None:
    if message is None:
        return None
    compact = " ".join(message.split())
    sanitized = _strip_absolute_paths(compact)
    if len(sanitized) > 400:
        return sanitized[:397] + "..."
    return sanitized


def _strip_absolute_paths(value: str) -> str:
    without_posix = re.sub(r"(?<!\w)/(?:[^/\s]+/)+[^/\s]+", "<path>", value)
    return re.sub(
        r"(?<!\w)[A-Za-z]:\\(?:[^\\\s]+\\)+[^\\\s]+",
        "<path>",
        without_posix,
    )


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(tz=value.tzinfo).isoformat().replace("+00:00", "Z")
