"""Technical Debt Intelligence pack identifiers."""

from __future__ import annotations

PACK_ID = "technical_debt.core"
PACK_VERSION = "1.0.0"
PACK_TITLE = "Technical Debt Intelligence Core"
PACK_DESCRIPTION = (
    "Technical Debt Intelligence SharedRule pack. Phase 4.3.3 registers "
    "deterministic complexity rules that consume Language Evidence complexity "
    "facts. Assessment synthesis and report integration remain deferred."
)

RULE_ID_PREFIX = "technical_debt."

TAXONOMY_NAMESPACE = "technical-debt"

RULE_LARGE_CALLABLE = "technical_debt.large-callable"
RULE_EXCESSIVE_BRANCHING = "technical_debt.excessive-branching"
RULE_DEEP_NESTING = "technical_debt.deep-nesting"
RULE_EXCESSIVE_PARAMETERS = "technical_debt.excessive-parameters"
RULE_OVERSIZED_TYPE = "technical_debt.oversized-type"

COMPLEXITY_RULE_IDS: tuple[str, ...] = (
    RULE_LARGE_CALLABLE,
    RULE_EXCESSIVE_BRANCHING,
    RULE_DEEP_NESTING,
    RULE_EXCESSIVE_PARAMETERS,
    RULE_OVERSIZED_TYPE,
)
