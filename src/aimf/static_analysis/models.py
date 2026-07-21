"""Provider-neutral static-analysis domain models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from aimf.models.finding import Finding
from aimf.models.repository import Repository
from aimf.models.technology import Technology


class StaticAnalysisStatus(StrEnum):
    """Execution outcome for an external static-analysis provider."""

    COMPLETED = "completed"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class StaticAnalysisContext(BaseModel):
    """Resolved inputs passed to a static-analysis provider."""

    repository: Repository
    repository_path: str
    detected_technologies: list[Technology] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    output_directory: str | None = None


class StaticAnalysisResult(BaseModel):
    """Outcome of one external static-analysis provider execution."""

    provider_id: str
    provider_name: str
    provider_version: str | None = None
    status: StaticAnalysisStatus
    findings: list[Finding] = Field(default_factory=list)
    files_analyzed: int = 0
    duration_ms: float | None = None
    command_metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None
