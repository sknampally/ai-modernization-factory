"""Shared Rule Platform contract (Phase 4+).

Distinct from the Assessment Graph :class:`~aimf.domain.rules.models.Rule`
protocol used by the production ``RuleEngine`` / ``aimf assess`` path.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aimf.domain.rules.applicability import RuleApplicability
from aimf.domain.rules.context import RuleExecutionContext
from aimf.domain.rules.metadata import RuleMetadata
from aimf.domain.rules.results import SharedRuleEvaluationResult


@runtime_checkable
class SharedRule(Protocol):
    """Deterministic shared-rule contract for Analysis Intelligence packs."""

    @property
    def metadata(self) -> RuleMetadata:
        """Immutable rule metadata with stable ID and version."""

    def evaluate_applicability(self, context: RuleExecutionContext) -> RuleApplicability:
        """Return whether the rule should evaluate against this context."""

    def evaluate(self, context: RuleExecutionContext) -> SharedRuleEvaluationResult:
        """Evaluate the rule without I/O, AI, or persistence access."""
