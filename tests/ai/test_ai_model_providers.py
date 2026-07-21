"""Tests for AIMF AI model providers and Bedrock integration."""

from __future__ import annotations

import importlib
import json
import sys
from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError
from pydantic import ValidationError

from aimf.ai.contracts.models import (
    LLMAnalysisContext,
    LLMFindingEvidence,
    LLMMetricsContext,
    LLMRepositoryContext,
    LLMSectionTruncation,
)
from aimf.ai.prompts import ModernizationPromptBuilder
from aimf.ai.prompts.models import PromptMessage, PromptMetadata, PromptRequest
from aimf.ai.providers import (
    AIModelProvider,
    AIProviderInvocationError,
    AIProviderTimeoutError,
    AIResponseParsingError,
    AIResponseValidationError,
    BedrockAIModelProvider,
    ModelInvocationMetadata,
    ModelInvocationOptions,
    ModelInvocationResult,
    ModelUsage,
    ModernizationModelRequest,
    parse_recommendation_response,
)
from aimf.ai.providers import bedrock as bedrock_module
from aimf.ai.providers.bedrock import (
    ANTHROPIC_BEDROCK_VERSION,
    build_anthropic_bedrock_payload,
)
from aimf.ai.providers.parsing import sanitize_provider_text
from aimf.ai.recommendations import (
    AIRecommendation,
    AIRecommendationConfidence,
    AIRecommendationEffort,
    AIRecommendationImpact,
    AIRecommendationPriority,
    AIRecommendationResult,
    EvidenceCoverage,
    ModernizationPhase,
    ai_recommendation_result_to_json,
)


def _truncation(count: int = 0, *, truncated: bool = False) -> LLMSectionTruncation:
    return LLMSectionTruncation(
        truncated=truncated,
        original_count=count,
        included_count=count,
    )


def _context(*rule_ids: str) -> LLMAnalysisContext:
    findings = [
        LLMFindingEvidence(
            rule_id=rule_id,
            title=f"Finding {rule_id}",
            category="security",
            severity="high",
            summary=f"Summary {rule_id}",
            evidence_truncation=_truncation(),
        )
        for rule_id in rule_ids
    ]
    return LLMAnalysisContext(
        repository=LLMRepositoryContext(
            name="sample-app",
            source_type="github",
            file_count=3,
        ),
        metrics=LLMMetricsContext(
            finding_count=len(findings),
            technology_count=0,
        ),
        findings=findings,
        findings_truncation=_truncation(len(findings)),
    )


def _recommendation(
    recommendation_id: str,
    *,
    related: list[str] | None = None,
    dependencies: list[str] | None = None,
) -> AIRecommendation:
    return AIRecommendation(
        recommendation_id=recommendation_id,
        title=f"Title {recommendation_id}",
        description=f"Description {recommendation_id}",
        rationale=f"Rationale {recommendation_id}",
        priority=AIRecommendationPriority.HIGH,
        effort=AIRecommendationEffort.MEDIUM,
        impact=AIRecommendationImpact.HIGH,
        confidence=AIRecommendationConfidence.MEDIUM,
        related_finding_ids=related or [],
        suggested_actions=["Take action"],
        dependencies=dependencies or [],
    )


def _valid_result() -> AIRecommendationResult:
    return AIRecommendationResult(
        executive_summary="Executive summary.",
        overall_assessment="Overall assessment.",
        key_risks=["Secret exposure"],
        recommendations=[
            _recommendation("REC-001", related=["SEC001"]),
            _recommendation("REC-002", related=["SEC002"], dependencies=["REC-001"]),
        ],
        modernization_phases=[
            ModernizationPhase(
                phase=1,
                name="Stabilize",
                objective="Address critical gaps",
                recommendations=["REC-001"],
                expected_outcomes=["Lower risk"],
            ),
            ModernizationPhase(
                phase=2,
                name="Hardening",
                objective="Continue modernization",
                recommendations=["REC-002"],
                expected_outcomes=["Safer releases"],
            ),
        ],
        evidence_coverage=EvidenceCoverage(
            total_findings=2,
            findings_considered=2,
            findings_referenced=2,
            coverage_percentage=100.0,
            input_truncated=False,
        ),
        limitations=["No runtime profiling data."],
    )


def _prompt_request(context: LLMAnalysisContext) -> PromptRequest:
    return ModernizationPromptBuilder().build(context)


def _model_request(context: LLMAnalysisContext | None = None) -> ModernizationModelRequest:
    analysis_context = context or _context("SEC001", "SEC002")
    return ModernizationModelRequest(
        prompt_request=_prompt_request(analysis_context),
        analysis_context=analysis_context,
    )


def _options(
    *,
    model_id: str = "anthropic.claude-test-model",
    temperature: float = 0.0,
    max_output_tokens: int = 2048,
    timeout_seconds: float = 30.0,
    request_id: str | None = None,
) -> ModelInvocationOptions:
    return ModelInvocationOptions(
        model_id=model_id,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
        request_id=request_id,
    )


def _bedrock_response(
    text: str,
    *,
    input_tokens: int = 11,
    output_tokens: int = 22,
    stop_reason: str = "end_turn",
    request_id: str = "req-123",
) -> dict[str, Any]:
    body = {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude",
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }
    return {
        "body": BytesIO(json.dumps(body).encode("utf-8")),
        "ResponseMetadata": {"RequestId": request_id},
    }


def _client_error(code: str, message: str = "boom") -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"RequestId": "err-1"},
        },
        "InvokeModel",
    )


class _FakeProvider(AIModelProvider):
    def invoke(
        self,
        request: ModernizationModelRequest,
        options: ModelInvocationOptions,
    ) -> ModelInvocationResult:
        return ModelInvocationResult(
            recommendation_result=_valid_result(),
            metadata=ModelInvocationMetadata(
                provider="fake",
                model_id=options.model_id,
                request_id=options.request_id,
                latency_ms=1.0,
                usage=ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2),
                stop_reason="end",
            ),
            raw_response_text="{}",
        )


def test_provider_abstraction() -> None:
    provider: AIModelProvider = _FakeProvider()
    result = provider.invoke(_model_request(), _options())
    assert result.metadata.provider == "fake"
    assert result.recommendation_result.recommendations[0].recommendation_id == "REC-001"


def test_successful_bedrock_invocation() -> None:
    client = MagicMock()
    client.invoke_model.return_value = _bedrock_response(
        ai_recommendation_result_to_json(_valid_result(), indent=None)
    )
    provider = BedrockAIModelProvider(client=client)
    request = _model_request()
    result = provider.invoke(request, _options(request_id="client-req"))

    assert result.recommendation_result == _valid_result()
    assert result.metadata.provider == "bedrock"
    assert result.metadata.model_id == "anthropic.claude-test-model"
    assert result.metadata.request_id == "client-req"
    assert result.metadata.stop_reason == "end_turn"
    assert result.metadata.usage == ModelUsage(
        input_tokens=11,
        output_tokens=22,
        total_tokens=33,
    )
    assert result.metadata.latency_ms >= 0.0
    assert result.raw_response_text
    client.invoke_model.assert_called_once()


def test_deterministic_payload_construction() -> None:
    request = _model_request()
    options = _options(temperature=0.0, max_output_tokens=1024)
    first = build_anthropic_bedrock_payload(request.prompt_request, options)
    second = build_anthropic_bedrock_payload(request.prompt_request, options)
    assert first == second
    assert first["anthropic_version"] == ANTHROPIC_BEDROCK_VERSION
    assert first["temperature"] == 0.0
    assert first["max_tokens"] == 1024
    assert first["messages"][0]["role"] == "user"


def test_system_developer_user_message_mapping() -> None:
    prompt = PromptRequest(
        messages=[
            PromptMessage(role="system", content="System rules"),
            PromptMessage(role="developer", content="Developer rules"),
            PromptMessage(role="user", content="Assess this repository"),
        ],
        context_json="{}",
        expected_output_schema_json="{}",
        metadata=PromptMetadata(
            repository_identifier="sample-app",
            context_schema_version="1.0.0",
            recommendation_schema_version="1.0.0",
            finding_count=0,
            technology_count=0,
            context_truncated=False,
            prompt_template_version="1.0.0",
        ),
    )
    payload = build_anthropic_bedrock_payload(prompt, _options())
    assert payload["system"] == "System rules"
    user_content = payload["messages"][0]["content"]
    assert user_content.startswith("Developer instructions:\nDeveloper rules")
    assert "Assess this repository" in user_content
    assert "single JSON object only" in user_content


def test_configurable_model_id() -> None:
    client = MagicMock()
    client.invoke_model.return_value = _bedrock_response(
        ai_recommendation_result_to_json(_valid_result(), indent=None)
    )
    provider = BedrockAIModelProvider(client=client)
    provider.invoke(_model_request(), _options(model_id="custom.model-id"))
    assert client.invoke_model.call_args.kwargs["modelId"] == "custom.model-id"


def test_temperature_and_token_options() -> None:
    client = MagicMock()
    client.invoke_model.return_value = _bedrock_response(
        ai_recommendation_result_to_json(_valid_result(), indent=None)
    )
    provider = BedrockAIModelProvider(client=client)
    provider.invoke(
        _model_request(),
        _options(temperature=0.2, max_output_tokens=512),
    )
    body = json.loads(client.invoke_model.call_args.kwargs["body"])
    assert body["temperature"] == 0.2
    assert body["max_tokens"] == 512


def test_strict_json_parsing() -> None:
    context = _context("SEC001", "SEC002")
    payload = ai_recommendation_result_to_json(_valid_result(), indent=None)
    parsed = parse_recommendation_response(f"  {payload}  ", context)
    assert parsed == _valid_result()


def test_fenced_json_parsing() -> None:
    context = _context("SEC001", "SEC002")
    payload = ai_recommendation_result_to_json(_valid_result(), indent=2)
    fenced = f"```json\n{payload}\n```"
    parsed = parse_recommendation_response(fenced, context)
    assert parsed == _valid_result()


def test_prose_rejection() -> None:
    context = _context("SEC001", "SEC002")
    payload = ai_recommendation_result_to_json(_valid_result(), indent=None)
    with pytest.raises(AIResponseParsingError, match="single JSON object"):
        parse_recommendation_response(f"Here you go:\n{payload}", context)


def test_malformed_json() -> None:
    with pytest.raises(AIResponseParsingError):
        parse_recommendation_response("{not-json", _context("SEC001"))


def test_multiple_object_rejection() -> None:
    with pytest.raises(AIResponseParsingError, match="exactly one JSON object"):
        parse_recommendation_response('{"a": 1}{"b": 2}', _context())


def test_invalid_recommendation_schema() -> None:
    with pytest.raises(AIResponseValidationError, match="AIRecommendationResult"):
        parse_recommendation_response('{"executive_summary": "only"}', _context())


def test_invalid_finding_references() -> None:
    result = _valid_result()
    broken = result.model_dump(mode="json")
    broken["recommendations"][0]["related_finding_ids"] = ["MISSING"]
    with pytest.raises(AIResponseValidationError, match="context-aware"):
        parse_recommendation_response(json.dumps(broken), _context("SEC001", "SEC002"))


def test_invalid_dependency_and_phase_references() -> None:
    with pytest.raises(AIResponseValidationError):
        parse_recommendation_response(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "executive_summary": "Summary",
                    "overall_assessment": "Assessment",
                    "recommendations": [
                        {
                            "recommendation_id": "REC-001",
                            "title": "Title",
                            "description": "Description",
                            "rationale": "Rationale",
                            "priority": "high",
                            "effort": "medium",
                            "impact": "high",
                            "confidence": "medium",
                            "related_finding_ids": [],
                            "suggested_actions": ["Act"],
                            "dependencies": ["REC-999"],
                        }
                    ],
                    "modernization_phases": [],
                    "evidence_coverage": {
                        "total_findings": 0,
                        "findings_considered": 0,
                        "findings_referenced": 0,
                        "coverage_percentage": 0.0,
                        "input_truncated": False,
                    },
                    "limitations": [],
                }
            ),
            _context(),
        )

    with pytest.raises(AIResponseValidationError):
        parse_recommendation_response(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "executive_summary": "Summary",
                    "overall_assessment": "Assessment",
                    "recommendations": [
                        {
                            "recommendation_id": "REC-001",
                            "title": "Title",
                            "description": "Description",
                            "rationale": "Rationale",
                            "priority": "high",
                            "effort": "medium",
                            "impact": "high",
                            "confidence": "medium",
                            "related_finding_ids": [],
                            "suggested_actions": ["Act"],
                            "dependencies": [],
                        }
                    ],
                    "modernization_phases": [
                        {
                            "phase": 1,
                            "name": "Phase",
                            "objective": "Objective",
                            "recommendations": ["REC-999"],
                            "expected_outcomes": [],
                        }
                    ],
                    "evidence_coverage": {
                        "total_findings": 0,
                        "findings_considered": 0,
                        "findings_referenced": 0,
                        "coverage_percentage": 0.0,
                        "input_truncated": False,
                    },
                    "limitations": [],
                }
            ),
            _context(),
        )


def test_usage_latency_request_id_and_stop_reason() -> None:
    client = MagicMock()
    client.invoke_model.return_value = _bedrock_response(
        ai_recommendation_result_to_json(_valid_result(), indent=None),
        input_tokens=5,
        output_tokens=7,
        stop_reason="max_tokens",
        request_id="amzn-req-9",
    )
    provider = BedrockAIModelProvider(client=client)
    result = provider.invoke(_model_request(), _options())
    assert result.metadata.usage.total_tokens == 12
    assert result.metadata.stop_reason == "max_tokens"
    assert result.metadata.request_id == "amzn-req-9"
    assert result.metadata.latency_ms >= 0.0


def test_timeout_mapping() -> None:
    client = MagicMock()
    client.invoke_model.side_effect = ReadTimeoutError(endpoint_url="https://example")
    provider = BedrockAIModelProvider(client=client)
    with pytest.raises(AIProviderTimeoutError, match="timed out"):
        provider.invoke(_model_request(), _options())


def test_throttling_mapping() -> None:
    client = MagicMock()
    client.invoke_model.side_effect = _client_error("ThrottlingException", "slow down")
    provider = BedrockAIModelProvider(client=client)
    with pytest.raises(AIProviderInvocationError, match="throttling"):
        provider.invoke(_model_request(), _options())


def test_authentication_and_access_denied_mapping() -> None:
    client = MagicMock()
    provider = BedrockAIModelProvider(client=client)

    client.invoke_model.side_effect = _client_error(
        "UnrecognizedClientException",
        "AKIAIOSFODNN7EXAMPLE bad key",
    )
    with pytest.raises(AIProviderInvocationError, match="authentication") as auth_info:
        provider.invoke(_model_request(), _options())
    assert "AKIAIOSFODNN7EXAMPLE" not in str(auth_info.value)

    client.invoke_model.side_effect = _client_error("AccessDeniedException", "nope")
    with pytest.raises(AIProviderInvocationError, match="access denied"):
        provider.invoke(_model_request(), _options())


def test_generic_provider_failure_mapping() -> None:
    client = MagicMock()
    client.invoke_model.side_effect = RuntimeError("unexpected AKIAIOSFODNN7EXAMPLE")
    provider = BedrockAIModelProvider(client=client)
    with pytest.raises(AIProviderInvocationError, match="invocation failed") as info:
        provider.invoke(_model_request(), _options())
    assert "AKIAIOSFODNN7EXAMPLE" not in str(info.value)
    assert "[REDACTED]" in str(info.value)


def test_exception_sanitization() -> None:
    text = sanitize_provider_text(
        "token=AKIAIOSFODNN7EXAMPLE aws_secret_access_key=abcd1234 secret"
    )
    assert "AKIAIOSFODNN7EXAMPLE" not in text
    assert "abcd1234" not in text
    assert "[REDACTED]" in text


def test_injected_client_usage() -> None:
    client = MagicMock()
    client.invoke_model.return_value = _bedrock_response(
        ai_recommendation_result_to_json(_valid_result(), indent=None)
    )
    with patch("boto3.client") as factory:
        provider = BedrockAIModelProvider(client=client)
        provider.invoke(_model_request(), _options())
        factory.assert_not_called()
    client.invoke_model.assert_called_once()


def test_no_aws_client_creation_during_module_import() -> None:
    module_name = "aimf.ai.providers.bedrock"
    with patch("boto3.client") as factory:
        if module_name in sys.modules:
            importlib.reload(bedrock_module)
        else:
            importlib.import_module(module_name)
        factory.assert_not_called()


def test_frozen_contracts_and_extra_field_rejection() -> None:
    options = _options()
    usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
    metadata = ModelInvocationMetadata(
        provider="bedrock",
        model_id="model",
        request_id=None,
        latency_ms=1.0,
        usage=usage,
        stop_reason=None,
    )
    result = ModelInvocationResult(
        recommendation_result=_valid_result(),
        metadata=metadata,
        raw_response_text="{}",
    )
    with pytest.raises(ValidationError):
        options.temperature = 1.0
    with pytest.raises(ValidationError):
        result.raw_response_text = "changed"
    with pytest.raises(ValidationError):
        ModelInvocationOptions(model_id="m", temperature=0.0, unexpected=True)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ModelUsage(input_tokens=1, extra=True)  # type: ignore[call-arg]


def test_prompt_request_not_mutated() -> None:
    client = MagicMock()
    client.invoke_model.return_value = _bedrock_response(
        ai_recommendation_result_to_json(_valid_result(), indent=None)
    )
    request = _model_request()
    before = request.prompt_request.model_dump(mode="json")
    BedrockAIModelProvider(client=client).invoke(request, _options())
    assert request.prompt_request.model_dump(mode="json") == before


def test_validation_error_from_bedrock_service() -> None:
    client = MagicMock()
    client.invoke_model.side_effect = _client_error("ValidationException", "bad input")
    provider = BedrockAIModelProvider(client=client)
    with pytest.raises(AIProviderInvocationError, match="validation"):
        provider.invoke(_model_request(), _options())


def test_fenced_json_with_trailing_prose_rejected() -> None:
    payload = ai_recommendation_result_to_json(_valid_result(), indent=None)
    with pytest.raises(AIResponseParsingError):
        parse_recommendation_response(
            f"```json\n{payload}\n```\nthanks", _context("SEC001", "SEC002")
        )
