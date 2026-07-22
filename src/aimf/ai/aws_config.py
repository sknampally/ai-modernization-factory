"""Centralized AWS session and Bedrock Runtime client configuration."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol, cast

from aimf.config.settings import AimfSettings

logger = logging.getLogger(__name__)

AWS_PROFILE_ENV = "AWS_PROFILE"
AWS_REGION_ENV = "AWS_REGION"
AWS_DEFAULT_REGION_ENV = "AWS_DEFAULT_REGION"


class BedrockRuntimeClient(Protocol):
    """Minimal Bedrock Runtime client protocol for dependency injection."""

    def converse(self, **kwargs: Any) -> Any:
        """Invoke a Bedrock model via the Converse API."""


@dataclass(frozen=True, slots=True)
class ResolvedAwsConfig:
    """Resolved AWS profile and region for session construction."""

    profile: str | None
    region: str | None
    source_profile: str
    source_region: str


def resolve_aws_config(
    *,
    settings: AimfSettings | None = None,
    profile: str | None = None,
    region: str | None = None,
) -> ResolvedAwsConfig:
    """Resolve AWS profile/region from explicit args, settings, then environment.

    Precedence for profile:
    1. Explicit ``profile`` argument
    2. ``[aws].profile`` from AIMF settings
    3. ``AWS_PROFILE`` environment variable
    4. ``None`` (boto3 default credential chain)

    Precedence for region:
    1. Explicit ``region`` argument
    2. ``[aws].region`` from AIMF settings
    3. ``ai.bedrock.region`` from AIMF settings (legacy)
    4. ``AWS_REGION`` / ``AWS_DEFAULT_REGION``
    5. ``None`` (boto3 default chain / shared config)
    """

    resolved_profile, profile_source = _first_nonempty(
        (profile, "argument"),
        (_settings_aws_profile(settings), "aimf.toml [aws].profile"),
        (os.environ.get(AWS_PROFILE_ENV), f"environment {AWS_PROFILE_ENV}"),
    )
    if resolved_profile is None:
        profile_source = "boto3 default credential chain"

    resolved_region, region_source = _first_nonempty(
        (region, "argument"),
        (_settings_aws_region(settings), "aimf.toml [aws].region"),
        (_settings_bedrock_region(settings), "aimf.toml [ai.bedrock].region"),
        (os.environ.get(AWS_REGION_ENV), f"environment {AWS_REGION_ENV}"),
        (
            os.environ.get(AWS_DEFAULT_REGION_ENV),
            f"environment {AWS_DEFAULT_REGION_ENV}",
        ),
    )
    if resolved_region is None:
        region_source = "boto3 default region chain"

    return ResolvedAwsConfig(
        profile=resolved_profile,
        region=resolved_region,
        source_profile=profile_source,
        source_region=region_source,
    )


def create_bedrock_runtime_client(
    *,
    settings: AimfSettings | None = None,
    profile: str | None = None,
    region: str | None = None,
    timeout_seconds: float = 60.0,
    model_id: str | None = None,
) -> BedrockRuntimeClient:
    """Create the single shared Bedrock Runtime client used by AIMF.

    Never hardcodes credentials. Uses AIMF config, then environment variables,
    then the normal boto3 credential/provider chain.
    """

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    resolved = resolve_aws_config(settings=settings, profile=profile, region=region)
    _log_aws_session(resolved, model_id=model_id)

    try:
        import boto3
        from botocore.config import Config
        from botocore.exceptions import ProfileNotFound
    except ImportError as error:  # pragma: no cover - exercised when boto3 missing
        raise RuntimeError("boto3 is required to create a Bedrock Runtime client") from error

    read_timeout = max(1, int(timeout_seconds))
    connect_timeout = min(10, read_timeout)
    config = Config(
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries={"max_attempts": 1, "mode": "standard"},
    )

    session_kwargs: dict[str, Any] = {}
    if resolved.profile:
        session_kwargs["profile_name"] = resolved.profile
    if resolved.region:
        session_kwargs["region_name"] = resolved.region

    try:
        session = boto3.Session(**session_kwargs)
    except ProfileNotFound as error:
        raise AwsAuthenticationError(
            format_aws_authentication_error(profile=resolved.profile)
        ) from error
    except Exception as error:  # noqa: BLE001 - AWS boundary
        if _looks_like_auth_failure(error):
            raise AwsAuthenticationError(
                format_aws_authentication_error(profile=resolved.profile)
            ) from error
        raise

    client_kwargs: dict[str, Any] = {"config": config}
    if resolved.region:
        client_kwargs["region_name"] = resolved.region

    try:
        client = session.client("bedrock-runtime", **client_kwargs)
    except Exception as error:  # noqa: BLE001 - AWS boundary
        if _looks_like_auth_failure(error):
            raise AwsAuthenticationError(
                format_aws_authentication_error(profile=resolved.profile)
            ) from error
        raise

    return cast(BedrockRuntimeClient, client)


class AwsAuthenticationError(RuntimeError):
    """Raised when AWS authentication/profile resolution fails."""


def format_aws_authentication_error(*, profile: str | None = None) -> str:
    """Return a friendly AWS authentication guidance message for CLI users."""

    profile_label = profile.strip() if profile and profile.strip() else "<profile>"
    return (
        "Unable to authenticate with AWS.\n"
        "\n"
        "Try one of:\n"
        "\n"
        f"- aws sso login --profile {profile_label}\n"
        "- aws configure sso\n"
        "- configure AWS credentials"
    )


def _settings_aws_profile(settings: AimfSettings | None) -> str | None:
    if settings is None:
        return None
    return settings.aws.profile


def _settings_aws_region(settings: AimfSettings | None) -> str | None:
    if settings is None:
        return None
    return settings.aws.region


def _settings_bedrock_region(settings: AimfSettings | None) -> str | None:
    if settings is None:
        return None
    return settings.ai.bedrock.region


def _first_nonempty(
    *candidates: tuple[str | None, str],
) -> tuple[str | None, str]:
    for value, source in candidates:
        if value is None:
            continue
        compact = value.strip()
        if compact:
            return compact, source
    return None, "unset"


def _log_aws_session(resolved: ResolvedAwsConfig, *, model_id: str | None) -> None:
    profile_display = resolved.profile or "(default credential chain)"
    region_display = resolved.region or "(boto3 default)"
    model_display = model_id.strip() if model_id and model_id.strip() else "(not set)"
    logger.info(
        "AWS session for Bedrock: profile=%s region=%s model_id=%s "
        "(profile_source=%s, region_source=%s)",
        profile_display,
        region_display,
        model_display,
        resolved.source_profile,
        resolved.source_region,
    )


def _looks_like_auth_failure(error: Exception) -> bool:
    name = type(error).__name__
    if name in {
        "ProfileNotFound",
        "NoCredentialsError",
        "PartialCredentialsError",
        "TokenRetrievalError",
        "UnauthorizedSSOTokenError",
        "SSOTokenLoadError",
    }:
        return True
    code = _client_error_code(error)
    if code in {
        "UnrecognizedClientException",
        "InvalidSignatureException",
        "ExpiredTokenException",
        "AuthFailure",
        "AccessDeniedException",
        "UnauthorizedOperation",
    }:
        return True
    message = str(error).lower()
    return any(
        token in message
        for token in (
            "unable to locate credentials",
            "expired token",
            "invalid security token",
            "not authorized",
            "sso",
            "authentication",
        )
    )


def _client_error_code(error: Exception) -> str | None:
    response = getattr(error, "response", None)
    if not isinstance(response, dict):
        return None
    error_payload = response.get("Error")
    if not isinstance(error_payload, dict):
        return None
    code = error_payload.get("Code")
    return str(code) if code is not None else None


__all__ = [
    "AWS_DEFAULT_REGION_ENV",
    "AWS_PROFILE_ENV",
    "AWS_REGION_ENV",
    "AwsAuthenticationError",
    "BedrockRuntimeClient",
    "ResolvedAwsConfig",
    "create_bedrock_runtime_client",
    "format_aws_authentication_error",
    "resolve_aws_config",
]
