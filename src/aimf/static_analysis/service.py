"""Orchestration for configured static-analysis providers."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

from aimf.models.finding import Finding
from aimf.models.repository import Repository
from aimf.models.technology import Technology
from aimf.static_analysis.exceptions import StaticAnalysisProviderError
from aimf.static_analysis.models import (
    StaticAnalysisContext,
    StaticAnalysisResult,
    StaticAnalysisStatus,
)
from aimf.static_analysis.ordering import deduplicate_findings, sort_findings
from aimf.static_analysis.provider import StaticAnalysisProvider

logger = logging.getLogger(__name__)


class StaticAnalysisService:
    """Execute configured external static-analysis providers."""

    def __init__(
        self,
        providers: Sequence[StaticAnalysisProvider],
        *,
        enabled: bool = False,
        fail_on_provider_error: bool = False,
    ) -> None:
        self._providers = list(providers)
        self._enabled = enabled
        self._fail_on_provider_error = fail_on_provider_error

    def analyze(
        self,
        *,
        repository: Repository,
        technologies: Sequence[Technology],
        configuration: dict[str, object] | None = None,
        output_directory: Path | None = None,
    ) -> tuple[list[StaticAnalysisResult], list[Finding]]:
        """Run applicable providers and return results plus merged findings."""

        if not self._enabled:
            return [], []

        context = StaticAnalysisContext(
            repository=repository,
            repository_path=str(repository.path),
            detected_technologies=list(technologies),
            configuration=configuration or {},
            output_directory=(str(output_directory) if output_directory is not None else None),
        )

        results: list[StaticAnalysisResult] = []
        findings: list[Finding] = []

        for provider in sorted(self._providers, key=lambda item: item.provider_id):
            result = self._run_provider(provider=provider, context=context)
            if result is None:
                continue

            results.append(result)
            findings.extend(result.findings)

            if self._fail_on_provider_error and result.status in {
                StaticAnalysisStatus.UNAVAILABLE,
                StaticAnalysisStatus.FAILED,
            }:
                raise StaticAnalysisProviderError(
                    provider.provider_id,
                    result.error_message or f"provider {result.status.value}",
                )

        merged = sort_findings(deduplicate_findings(findings))
        return results, merged

    def _run_provider(
        self,
        *,
        provider: StaticAnalysisProvider,
        context: StaticAnalysisContext,
    ) -> StaticAnalysisResult | None:
        if not provider.is_applicable(context):
            return None

        if not provider.is_available():
            result = StaticAnalysisResult(
                provider_id=provider.provider_id,
                provider_name=provider.display_name,
                status=StaticAnalysisStatus.UNAVAILABLE,
                error_message=(
                    f"{provider.display_name} executable was not found or "
                    "could not report a version."
                ),
                warnings=[f"{provider.display_name} was unavailable and was skipped."],
            )
            logger.warning(
                "Static-analysis provider unavailable",
                extra={"provider_id": provider.provider_id},
            )
            return result

        started = perf_counter()
        try:
            result = provider.analyze(context)
        except Exception as exc:  # noqa: BLE001 - provider boundary
            duration_ms = round((perf_counter() - started) * 1000, 2)
            logger.exception(
                "Static-analysis provider failed",
                extra={"provider_id": provider.provider_id},
            )
            return StaticAnalysisResult(
                provider_id=provider.provider_id,
                provider_name=provider.display_name,
                status=StaticAnalysisStatus.FAILED,
                duration_ms=duration_ms,
                error_message=str(exc),
                warnings=[f"{provider.display_name} failed: {exc}"],
            )

        if result.duration_ms is None:
            result = result.model_copy(
                update={
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                }
            )
        return result
