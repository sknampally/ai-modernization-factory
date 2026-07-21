"""AWS Bedrock Runtime provider for modernization assessment."""

from __future__ import annotations

import json
import time
from typing import Any, Protocol, cast

from aimf.ai.prompts.models import PromptMessage, PromptRequest
from aimf.ai.providers.base import AIModelProvider
from aimf.ai.providers.exceptions import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderInvocationError,
    AIProviderTimeoutError,
    AIResponseParsingError,
    AIResponseValidationError,
)
from aimf.ai.providers.models import (
    DEFAULT_TIMEOUT_SECONDS,
    ModelInvocationMetadata,
    ModelInvocationOptions,
    ModelInvocationResult,
    ModelUsage,
    ModernizationModelRequest,
)
from aimf.ai.providers.parsing import parse_recommendation_response, sanitize_provider_text

BEDROCK_PROVIDER_NAME = "bedrock"
ANTHROPIC_BEDROCK_VERSION = "bedrock-2023-05-31"


class BedrockRuntimeClient(Protocol):
    """Minimal Bedrock Runtime client protocol for dependency injection."""

    def invoke_model(self, **kwargs: Any) -> Any:
        """Invoke a Bedrock model and return a response object."""


class BedrockAIModelProvider(AIModelProvider):
    """Invoke Anthropic Claude Messages API models hosted on AWS Bedrock."""

    def __init__(
        self,
        *,
        client: BedrockRuntimeClient | None = None,
        region_name: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise AIProviderConfigurationError("timeout_seconds must be positive")
        self._region_name = region_name
        self._client = (
            client
            if client is not None
            else _create_default_client(region_name, timeout_seconds=timeout_seconds)
        )

    def invoke(
        self,
        request: ModernizationModelRequest,
        options: ModelInvocationOptions,
    ) -> ModelInvocationResult:
        """Invoke Bedrock and return a validated recommendation result."""

        model_id = options.model_id.strip()
        if not model_id:
            raise AIProviderConfigurationError("model_id must be a nonempty string")

        body = build_anthropic_bedrock_payload(request.prompt_request, options)
        started = time.perf_counter()
        try:
            response = self._client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body, sort_keys=True, ensure_ascii=False),
            )
        except Exception as error:  # noqa: BLE001 - provider boundary
            raise _map_bedrock_exception(error) from error

        latency_ms = (time.perf_counter() - started) * 1000.0
        try:
            raw_response_text, usage, stop_reason, response_request_id = (
                _extract_anthropic_response(response)
            )
        except AIProviderError:
            raise
        except Exception as error:  # noqa: BLE001 - provider boundary
            raise AIProviderInvocationError(
                "Failed to read Bedrock response: " + sanitize_provider_text(str(error))
            ) from error

        try:
            recommendation_result = parse_recommendation_response(
                raw_response_text,
                request.analysis_context,
            )
        except (AIResponseParsingError, AIResponseValidationError):
            raise
        except Exception as error:  # noqa: BLE001 - provider boundary
            raise AIResponseParsingError(
                "Unexpected failure while parsing Bedrock response: "
                + sanitize_provider_text(str(error))
            ) from error

        request_id = options.request_id or response_request_id
        return ModelInvocationResult(
            recommendation_result=recommendation_result,
            metadata=ModelInvocationMetadata(
                provider=BEDROCK_PROVIDER_NAME,
                model_id=model_id,
                request_id=request_id,
                latency_ms=latency_ms,
                usage=usage,
                stop_reason=stop_reason,
            ),
            raw_response_text=raw_response_text,
        )


def build_anthropic_bedrock_payload(
    prompt_request: PromptRequest,
    options: ModelInvocationOptions,
) -> dict[str, Any]:
    """Deterministically convert PromptRequest into an Anthropic Bedrock body."""

    system_text, messages = _split_prompt_messages(prompt_request.messages)
    payload: dict[str, Any] = {
        "anthropic_version": ANTHROPIC_BEDROCK_VERSION,
        "max_tokens": options.max_output_tokens,
        "temperature": options.temperature,
        "messages": messages,
    }
    if system_text:
        payload["system"] = system_text
    return payload


def _split_prompt_messages(
    messages: list[PromptMessage],
) -> tuple[str | None, list[dict[str, str]]]:
    system_parts: list[str] = []
    conversation_parts: list[str] = []

    for message in messages:
        if message.role == "system":
            system_parts.append(message.content)
        elif message.role == "developer":
            conversation_parts.append(f"Developer instructions:\n{message.content}")
        elif message.role == "user":
            conversation_parts.append(message.content)
        else:  # pragma: no cover - Literal-protected
            raise AIProviderConfigurationError(f"Unsupported prompt role: {message.role}")

    system_text = "\n\n".join(system_parts) if system_parts else None
    if not conversation_parts:
        raise AIProviderConfigurationError(
            "PromptRequest must include at least one developer or user message"
        )

    # Anthropic Messages API requires alternating user/assistant turns.
    # Map developer + user into one deterministic user message.
    user_content = "\n\n".join(conversation_parts)
    user_content = (
        f"{user_content}\n\n"
        "Respond with a single JSON object only. Do not include markdown or prose."
    )
    return system_text, [{"role": "user", "content": user_content}]


def _create_default_client(
    region_name: str | None,
    *,
    timeout_seconds: float,
) -> BedrockRuntimeClient:
    try:
        import boto3
        from botocore.config import Config
    except ImportError as error:  # pragma: no cover - exercised when boto3 missing
        raise AIProviderConfigurationError(
            "boto3 is required to create a default Bedrock Runtime client"
        ) from error

    read_timeout = max(1, int(timeout_seconds))
    connect_timeout = min(10, read_timeout)
    config = Config(
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries={"max_attempts": 1, "mode": "standard"},
    )
    kwargs: dict[str, Any] = {
        "service_name": "bedrock-runtime",
        "config": config,
    }
    if region_name:
        kwargs["region_name"] = region_name
    return cast(BedrockRuntimeClient, boto3.client(**kwargs))


def _extract_anthropic_response(
    response: Any,
) -> tuple[str, ModelUsage, str | None, str | None]:
    body = _read_response_body(response)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise AIProviderInvocationError(
            "Bedrock returned a non-JSON response envelope: " + sanitize_provider_text(str(error))
        ) from error

    if not isinstance(payload, dict):
        raise AIProviderInvocationError("Bedrock response envelope must be a JSON object")

    raw_text = _extract_text_content(payload)
    usage_payload = payload.get("usage")
    usage = ModelUsage()
    if isinstance(usage_payload, dict):
        input_tokens = _optional_non_negative_int(usage_payload.get("input_tokens"))
        output_tokens = _optional_non_negative_int(usage_payload.get("output_tokens"))
        total_tokens: int | None = None
        if input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens
        usage = ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    stop_reason = payload.get("stop_reason")
    stop_reason_text = str(stop_reason) if stop_reason is not None else None

    request_id = None
    headers = getattr(response, "get", None)
    if callable(headers):
        # botocore ResponseMetadata lives on the response mapping.
        metadata = response.get("ResponseMetadata")
        if isinstance(metadata, dict):
            request_id_value = metadata.get("RequestId")
            if request_id_value is not None:
                request_id = str(request_id_value)

    return raw_text, usage, stop_reason_text, request_id


def _read_response_body(response: Any) -> str:
    if isinstance(response, dict):
        body = response.get("body")
    else:
        body = getattr(response, "body", None)

    if body is None:
        raise AIProviderInvocationError("Bedrock response is missing a body")

    if hasattr(body, "read"):
        raw = body.read()
    else:
        raw = body

    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    if isinstance(raw, str):
        return raw
    raise AIProviderInvocationError(
        f"Bedrock response body must be bytes or text, got {type(raw).__name__}"
    )


def _extract_text_content(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise AIProviderInvocationError("Bedrock Anthropic response is missing content blocks")

    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            text_parts.append(block["text"])

    if not text_parts:
        raise AIProviderInvocationError("Bedrock Anthropic response did not include text content")
    return "".join(text_parts)


def _optional_non_negative_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _map_bedrock_exception(error: Exception) -> AIProviderError:
    message = sanitize_provider_text(str(error))
    error_name = type(error).__name__
    error_code = _client_error_code(error)

    if error_name in {"ReadTimeoutError", "ConnectTimeoutError", "EndpointConnectionError"}:
        return AIProviderTimeoutError(f"Bedrock invocation timed out: {message}")

    if error_code in {
        "ThrottlingException",
        "TooManyRequestsException",
        "ServiceQuotaExceededException",
    }:
        return AIProviderInvocationError(f"Bedrock throttling error: {message}")

    if error_code in {
        "UnrecognizedClientException",
        "InvalidSignatureException",
        "ExpiredTokenException",
        "AuthFailure",
    }:
        return AIProviderInvocationError(f"Bedrock authentication error: {message}")

    if error_code in {"AccessDeniedException", "UnauthorizedOperation"}:
        return AIProviderInvocationError(f"Bedrock access denied: {message}")

    if error_code in {"ValidationException", "InvalidRequestException"}:
        return AIProviderInvocationError(f"Bedrock validation error: {message}")

    if error_code:
        return AIProviderInvocationError(f"Bedrock service error ({error_code}): {message}")

    return AIProviderInvocationError(f"Bedrock invocation failed: {message}")


def _client_error_code(error: Exception) -> str | None:
    response = getattr(error, "response", None)
    if not isinstance(response, dict):
        return None
    error_payload = response.get("Error")
    if not isinstance(error_payload, dict):
        return None
    code = error_payload.get("Code")
    return str(code) if code is not None else None
