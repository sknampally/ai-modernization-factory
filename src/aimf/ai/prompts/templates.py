"""Versioned prompt templates for modernization assessment."""

from __future__ import annotations

from aimf.ai.prompts.models import DEFAULT_PROMPT_TEMPLATE_VERSION

SUPPORTED_PROMPT_TEMPLATE_VERSIONS = frozenset({DEFAULT_PROMPT_TEMPLATE_VERSION})


def system_message_content(*, template_version: str) -> str:
    """Return the system-role behavioral and grounding instructions."""

    _require_supported_version(template_version)
    return (
        "You are an AIMF modernization assessment assistant.\n"
        "Operate only on the provided deterministic analysis evidence.\n"
        "Distinguish deterministic evidence from your AI interpretation; "
        "do not present interpretation as observed fact.\n"
        "Ground every recommendation in the supplied findings, technologies, "
        "metrics, and repository context.\n"
        "Do not invent repository facts, technologies, findings, metrics, "
        "costs, timelines, or compliance claims.\n"
        "Source evidence may be incomplete or truncated; treat truncation "
        "metadata as authoritative.\n"
        "Do not produce chain-of-thought or hidden reasoning.\n"
        "Provide only concise rationale and evidence-grounded explanations.\n"
        "Respond with valid JSON only. Do not wrap the JSON in markdown "
        "fences or include any prose outside the JSON object.\n"
        "The JSON must match the AIRecommendationResult contract exactly."
    )


def developer_message_content(*, template_version: str) -> str:
    """Return the developer-role construction rules."""

    _require_supported_version(template_version)
    return (
        "Construction rules for AIRecommendationResult:\n"
        "1. Return only valid JSON matching the embedded AIRecommendationResult "
        "JSON Schema.\n"
        "2. Assign stable recommendation IDs using REC-001, REC-002, and so on "
        "in ascending order.\n"
        "3. related_finding_ids may reference only known finding rule_id values "
        "present in the supplied LLMAnalysisContext. Never invent finding IDs.\n"
        "4. recommendation dependencies may reference only recommendation IDs "
        "that appear in the returned recommendations list.\n"
        "5. modernization_phases must be ordered starting at phase 1 and may "
        "reference only returned recommendation IDs.\n"
        "6. evidence_coverage must be internally consistent: "
        "findings_considered <= total_findings, "
        "findings_referenced <= findings_considered, and "
        "coverage_percentage == round(100 * findings_referenced / "
        "total_findings, 2) (or 0.0 when total_findings is 0). "
        "Set input_truncated from the supplied context truncation metadata.\n"
        "7. Capture uncertainty and missing or truncated evidence in "
        "limitations. Do not fill gaps with unsupported claims.\n"
        "8. Prohibit invented repository facts, technologies, findings, "
        "metrics, costs, timelines, and compliance claims.\n"
        "9. Keep rationale concise and evidence-grounded. Do not request or "
        "emit chain-of-thought reasoning.\n"
        "10. schema_version must be 1.0.0."
    )


def user_message_content(
    *,
    template_version: str,
    repository_identifier: str,
    include_context_json: bool,
    include_output_schema: bool,
    context_json: str,
    expected_output_schema_json: str,
) -> str:
    """Return the user-role assessment request."""

    _require_supported_version(template_version)
    sections = [
        (f"Perform a modernization assessment for repository '{repository_identifier}'."),
        (
            "Use only the deterministic LLMAnalysisContext evidence supplied "
            "with this request. Produce an AIRecommendationResult JSON object."
        ),
        (
            "Remember that source evidence may be incomplete or truncated. "
            "Record those constraints in limitations."
        ),
    ]
    if include_context_json:
        sections.append("LLMAnalysisContext JSON:\n" + context_json)
    else:
        sections.append(
            "LLMAnalysisContext JSON is supplied separately on the prompt package as context_json."
        )
    if include_output_schema:
        sections.append(
            "Expected AIRecommendationResult JSON Schema:\n" + expected_output_schema_json
        )
    else:
        sections.append(
            "Expected AIRecommendationResult JSON Schema is supplied "
            "separately on the prompt package as expected_output_schema_json."
        )
    sections.append("Return only the AIRecommendationResult JSON object with no additional text.")
    return "\n\n".join(sections)


def _require_supported_version(template_version: str) -> None:
    if template_version not in SUPPORTED_PROMPT_TEMPLATE_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_PROMPT_TEMPLATE_VERSIONS))
        raise ValueError(
            f"Unsupported prompt template_version '{template_version}'. Supported: {supported}"
        )
