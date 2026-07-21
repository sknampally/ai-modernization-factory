"""Map AnalysisResult into the LLM evidence contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aimf.ai.contracts.limits import LLMContractLimits
from aimf.ai.contracts.models import (
    LLM_CONTRACT_SCHEMA_VERSION,
    LLMAnalysisContext,
    LLMEvidenceLocation,
    LLMFindingEvidence,
    LLMMetricsContext,
    LLMRepositoryContext,
    LLMSectionTruncation,
    LLMTechnologyEvidence,
)
from aimf.models import AnalysisResult, Finding, Technology
from aimf.models.enums import Severity
from aimf.models.evidence import Evidence
from aimf.security.redaction import Redactor

_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

_EXCLUDED_METADATA_KEYS = frozenset(
    {
        "token",
        "password",
        "secret",
        "credential",
        "credentials",
        "authorization",
        "askpass",
        "private_key",
        "api_key",
        "access_token",
        "refresh_token",
        "token_env",
        "executable",
        "command",
        "argv",
        "environment",
        "env",
        "temp_report",
        "output_directory",
        "workspace",
        "helper_path",
        "git_askpass",
    }
)

_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?i)(?:^|[\s\"'=])(/Users/|/home/|/tmp/|/var/|/private/|[A-Za-z]:\\)"
)


class LLMAnalysisContextBuilder:
    """Build a deterministic LLMAnalysisContext from an AnalysisResult."""

    def __init__(
        self,
        *,
        limits: LLMContractLimits | None = None,
        redactor: Redactor | None = None,
    ) -> None:
        self._limits = limits or LLMContractLimits()
        self._redactor = redactor or Redactor()

    def build(self, result: AnalysisResult) -> LLMAnalysisContext:
        """Convert an AnalysisResult into an immutable LLM contract."""

        technologies = self._map_technologies(result.technologies)
        findings, findings_truncation = self._map_findings(result.findings)
        repository = self._map_repository(result)
        metrics = LLMMetricsContext(
            file_count=self._file_count(result),
            source_file_count=(
                result.facts.structure.source_file_count
                if result.facts.structure is not None
                else None
            ),
            test_file_count=(
                result.facts.structure.test_file_count
                if result.facts.structure is not None
                else None
            ),
            finding_count=len(result.findings),
            technology_count=len(result.technologies),
        )

        return LLMAnalysisContext(
            schema_version=LLM_CONTRACT_SCHEMA_VERSION,
            repository=repository,
            technologies=technologies,
            metrics=metrics,
            findings=findings,
            findings_truncation=findings_truncation,
        )

    def _map_repository(self, result: AnalysisResult) -> LLMRepositoryContext:
        repository = result.repository
        file_count = self._file_count(result)
        commit_sha = self._safe_commit_sha(repository.metadata)

        return LLMRepositoryContext(
            name=self._sanitize_text(repository.name) or "unknown",
            source_type=self._source_type(repository.source_url),
            default_branch=self._sanitize_optional_text(repository.default_branch),
            commit_sha=commit_sha,
            file_count=file_count,
        )

    def _file_count(self, result: AnalysisResult) -> int:
        if result.repository.total_files is not None:
            return result.repository.total_files
        if result.facts.structure is not None and result.facts.structure.file_count is not None:
            return result.facts.structure.file_count
        return len(result.repository.files)

    def _source_type(self, source_url: str | None) -> str:
        if not source_url:
            return "local"
        lowered = source_url.lower()
        if "github.com" in lowered:
            return "github"
        if lowered.startswith("http://") or lowered.startswith("https://"):
            return "remote"
        if lowered.startswith("git@") or lowered.startswith("ssh://"):
            return "remote"
        return "unknown"

    def _safe_commit_sha(self, metadata: dict[str, Any]) -> str | None:
        raw = metadata.get("commit_sha") or metadata.get("commit")
        if not isinstance(raw, str):
            return None
        compact = raw.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{7,40}", compact):
            return None
        return compact.lower()

    def _map_technologies(
        self,
        technologies: list[Technology],
    ) -> list[LLMTechnologyEvidence]:
        ordered = sorted(
            technologies,
            key=lambda item: (
                self._enum_value(item.category),
                item.name.lower(),
                (item.version or "").lower(),
            ),
        )
        mapped: list[LLMTechnologyEvidence] = []
        for technology in ordered:
            evidence_items: list[str] = []
            if technology.source:
                sanitized_source = self._sanitize_text(technology.source)
                if sanitized_source:
                    evidence_items.append(sanitized_source)
            mapped.append(
                LLMTechnologyEvidence(
                    name=self._sanitize_text(technology.name) or technology.name,
                    category=self._enum_value(technology.category),
                    version=self._sanitize_optional_text(technology.version),
                    confidence=technology.confidence,
                    evidence=evidence_items,
                )
            )
        return mapped

    def _map_findings(
        self,
        findings: list[Finding],
    ) -> tuple[list[LLMFindingEvidence], LLMSectionTruncation]:
        ordered = sorted(
            findings,
            key=lambda finding: (
                _SEVERITY_ORDER.get(finding.severity, 99),
                self._enum_value(finding.category),
                (finding.rule_id or "").lower(),
                finding.title.lower(),
            ),
        )
        original_count = len(ordered)
        included = ordered[: self._limits.max_findings]
        mapped = [self._map_finding(finding) for finding in included]
        truncation = LLMSectionTruncation(
            truncated=original_count > len(included),
            original_count=original_count,
            included_count=len(included),
        )
        return mapped, truncation

    def _map_finding(self, finding: Finding) -> LLMFindingEvidence:
        evidence_items, evidence_truncation = self._map_evidence(finding.evidence)
        affected = sorted(
            {
                sanitized
                for item in finding.affected_technologies
                if (sanitized := self._sanitize_text(item))
            },
            key=str.lower,
        )
        return LLMFindingEvidence(
            rule_id=self._sanitize_optional_text(finding.rule_id),
            title=self._sanitize_text(finding.title) or finding.title,
            category=self._enum_value(finding.category),
            severity=self._enum_value(finding.severity),
            summary=self._sanitize_text(finding.description) or "",
            evidence=evidence_items,
            affected_technologies=affected,
            metadata=self._map_metadata(finding.metadata),
            evidence_truncation=evidence_truncation,
        )

    def _map_evidence(
        self,
        evidence_items: list[Evidence],
    ) -> tuple[list[LLMEvidenceLocation], LLMSectionTruncation]:
        ordered = sorted(
            evidence_items,
            key=lambda item: (
                item.file_path,
                item.line_number or 0,
                item.column_number or 0,
                item.description or "",
            ),
        )
        original_count = len(ordered)
        included = ordered[: self._limits.max_evidence_per_finding]
        mapped = [self._map_evidence_item(item) for item in included]
        truncation = LLMSectionTruncation(
            truncated=original_count > len(included),
            original_count=original_count,
            included_count=len(included),
        )
        return mapped, truncation

    def _map_evidence_item(self, item: Evidence) -> LLMEvidenceLocation:
        path = item.file_path.strip() if item.file_path else "."
        # Preserve repository-root contract paths exactly.
        if path in {".", "./"}:
            path = "."
        else:
            path = self._repository_relative_path(path)

        excerpt_source = item.snippet or item.description or item.detected_value
        excerpt = self._truncate_excerpt(excerpt_source)

        return LLMEvidenceLocation(
            path=path,
            line=item.line_number,
            column=item.column_number,
            excerpt=excerpt,
        )

    def _map_metadata(self, metadata: dict[str, Any]) -> dict[str, str]:
        mapped: dict[str, str] = {}
        for key in sorted(metadata.keys(), key=str.lower):
            if not isinstance(key, str):
                continue
            if self._is_excluded_metadata_key(key):
                continue
            value = metadata[key]
            if value is None:
                continue
            if isinstance(value, (dict, list, tuple, set)):
                continue
            text = self._sanitize_text(str(value))
            if text is None:
                continue
            mapped[key] = self._truncate_metadata_value(text)
        return mapped

    def _is_excluded_metadata_key(self, key: str) -> bool:
        normalized = key.strip().lower().replace("-", "_")
        if normalized in _EXCLUDED_METADATA_KEYS:
            return True
        return any(
            token in normalized
            for token in (
                "token",
                "password",
                "secret",
                "credential",
                "askpass",
                "private_key",
                "api_key",
            )
        )

    def _truncate_excerpt(self, value: str | None) -> str | None:
        if value is None:
            return None
        sanitized = self._sanitize_text(value)
        if sanitized is None:
            return None
        limit = self._limits.max_excerpt_characters
        if len(sanitized) <= limit:
            return sanitized
        if limit == 0:
            return ""
        return sanitized[:limit]

    def _truncate_metadata_value(self, value: str) -> str:
        limit = self._limits.max_metadata_value_characters
        if len(value) <= limit:
            return value
        if limit == 0:
            return ""
        return value[:limit]

    def _repository_relative_path(self, path: str) -> str:
        candidate = path.strip().replace("\\", "/")
        if candidate.startswith("./"):
            candidate = candidate[2:]
        # Never emit absolute filesystem paths into the contract.
        if Path(candidate).is_absolute() or _ABSOLUTE_PATH_PATTERN.search(f" {candidate}"):
            return Path(candidate).name or "."
        sanitized = self._sanitize_text(candidate)
        return sanitized or "."

    def _sanitize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        return self._sanitize_text(value)

    def _sanitize_text(self, value: str) -> str | None:
        compact = value.strip()
        if not compact:
            return None
        redacted = self._redactor.redact(compact)
        if _ABSOLUTE_PATH_PATTERN.search(f" {redacted}"):
            # Drop values that still look like local absolute paths after redaction.
            return None
        lowered = redacted.lower()
        if any(
            marker in lowered
            for marker in (
                "aimf-askpass",
                "aimf-git-auth",
                "git_askpass",
                "token_env",
            )
        ):
            return None
        return redacted

    def _enum_value(self, value: Any) -> str:
        raw = getattr(value, "value", value)
        return str(raw).lower()
