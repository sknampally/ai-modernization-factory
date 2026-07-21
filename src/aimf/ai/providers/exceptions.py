"""Typed exceptions for AIMF AI model providers."""

from __future__ import annotations


class AIProviderError(Exception):
    """Base error for AI model provider failures."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when a provider is misconfigured or unavailable."""


class AIProviderInvocationError(AIProviderError):
    """Raised when a provider invocation fails."""


class AIProviderTimeoutError(AIProviderInvocationError):
    """Raised when a provider invocation times out."""


class AIResponseParsingError(AIProviderError):
    """Raised when a model response cannot be parsed as the required contract."""


class AIResponseValidationError(AIProviderError):
    """Raised when parsed model output fails contract or context validation."""
