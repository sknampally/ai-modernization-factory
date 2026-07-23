"""Phase 3 graph-rule finding enumerations.

Distinct from Phase 1 ``aimf.models`` findings, which use UUID identities and
analyzer pipelines. These enums describe Assessment-Graph rule findings only.
"""

from __future__ import annotations

from enum import StrEnum


class FindingSeverity(StrEnum):
    """Severity for graph-rule findings."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(StrEnum):
    """Category for graph-rule findings."""

    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    BUILD = "build"
    GOVERNANCE = "governance"
    MODERNIZATION = "modernization"
    UNKNOWN = "unknown"


class FindingSource(StrEnum):
    """Origin of a Phase 3 finding."""

    RULE = "rule"
