"""Immutable LLM evidence contract models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

LLM_CONTRACT_SCHEMA_VERSION = "1.0.0"


class LLMSectionTruncation(BaseModel):
    """Explicit truncation metadata for a contract collection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    truncated: bool = False
    original_count: int = Field(ge=0)
    included_count: int = Field(ge=0)


class LLMEvidenceLocation(BaseModel):
    """Repository-relative evidence location for LLM consumption."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    excerpt: str | None = None


class LLMTechnologyEvidence(BaseModel):
    """Detected technology evidence for LLM consumption."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    category: str
    version: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class LLMFindingEvidence(BaseModel):
    """Finding evidence for LLM consumption."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str | None = None
    title: str
    category: str
    severity: str
    summary: str
    evidence: list[LLMEvidenceLocation] = Field(default_factory=list)
    affected_technologies: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    evidence_truncation: LLMSectionTruncation


class LLMRepositoryContext(BaseModel):
    """Repository identity and inventory summary for LLM consumption."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    source_type: str
    default_branch: str | None = None
    commit_sha: str | None = None
    file_count: int = Field(ge=0)


class LLMMetricsContext(BaseModel):
    """Compact deterministic metrics derived from analysis facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file_count: int | None = None
    source_file_count: int | None = None
    test_file_count: int | None = None
    finding_count: int = Field(ge=0)
    technology_count: int = Field(ge=0)


class LLMAnalysisContext(BaseModel):
    """Provider-neutral LLM analysis evidence contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = LLM_CONTRACT_SCHEMA_VERSION
    repository: LLMRepositoryContext
    technologies: list[LLMTechnologyEvidence] = Field(default_factory=list)
    metrics: LLMMetricsContext
    findings: list[LLMFindingEvidence] = Field(default_factory=list)
    findings_truncation: LLMSectionTruncation

    def model_dump_json_ready(self) -> dict[str, Any]:
        """Return a JSON-ready dictionary using mode='json'."""

        return self.model_dump(mode="json")
