"""Rule contracts for Assessment Graph rules and Shared Rule Platform.

Legacy Assessment Graph contracts (``Rule``, ``RuleContext``, ``RuleResult``)
remain the production path for ``aimf assess``.

Phase 4 Shared Rule Platform types (``SharedRule``, ``RuleExecutionContext``,
…) are additive and disabled by default until Analysis Intelligence packs land.
"""

from aimf.domain.rules.applicability import (
    RuleApplicability,
    RuleSuppression,
    RuleSuppressionDecision,
)
from aimf.domain.rules.context import (
    DependencyFact,
    DependencyInventoryView,
    IncrementalChangeView,
    LanguageInventoryView,
    RepositoryFactView,
    RuleExecutionContext,
    RuleExecutionPolicy,
)
from aimf.domain.rules.contracts import SharedRule
from aimf.domain.rules.enums import (
    RuleApplicabilityStatus,
    RuleCategory,
    RuleConfidence,
    RuleEvidenceKind,
    RuleIncrementalBehavior,
    RuleResultStatus,
    RuleSeverity,
    RuleSkipReason,
    RuleSuppressionSource,
)
from aimf.domain.rules.evidence import RuleEvidence, dedupe_evidence, fingerprint_excerpt
from aimf.domain.rules.identifiers import RuleId, validate_rule_id
from aimf.domain.rules.metadata import RuleMetadata, RuleVersion
from aimf.domain.rules.models import Rule, RuleContext, RuleResult
from aimf.domain.rules.results import (
    RuleDiagnostic,
    RuleMatch,
    SharedRuleEvaluationResult,
)

__all__ = [
    "DependencyFact",
    "DependencyInventoryView",
    "IncrementalChangeView",
    "LanguageInventoryView",
    "RepositoryFactView",
    "Rule",
    "RuleApplicability",
    "RuleApplicabilityStatus",
    "RuleCategory",
    "RuleConfidence",
    "RuleContext",
    "RuleDiagnostic",
    "RuleEvidence",
    "RuleEvidenceKind",
    "RuleExecutionContext",
    "RuleExecutionPolicy",
    "RuleId",
    "RuleIncrementalBehavior",
    "RuleMatch",
    "RuleMetadata",
    "RuleResult",
    "RuleResultStatus",
    "RuleSeverity",
    "RuleSkipReason",
    "RuleSuppression",
    "RuleSuppressionDecision",
    "RuleSuppressionSource",
    "RuleVersion",
    "SharedRule",
    "SharedRuleEvaluationResult",
    "dedupe_evidence",
    "fingerprint_excerpt",
    "validate_rule_id",
]
