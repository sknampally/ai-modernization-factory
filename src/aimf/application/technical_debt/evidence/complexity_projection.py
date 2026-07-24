"""Thin Technical Debt projection over Language Evidence complexity facts.

Phase 4.3.2: no debt findings, thresholds, or scoring. Future debt rules may
consume ``AggregatedComplexityEvidence`` through this module without owning
parsers.
"""

from __future__ import annotations

from aimf.domain.evidence.language.complexity.models import AggregatedComplexityEvidence
from aimf.domain.technical_debt.taxonomy import TechnicalDebtCategory


def complexity_evidence_for_debt(
    evidence: AggregatedComplexityEvidence,
) -> AggregatedComplexityEvidence:
    """Return complexity evidence unchanged for future technical-debt rules."""

    return evidence


def complexity_taxonomy_category() -> TechnicalDebtCategory:
    """Taxonomy leaf future complexity debt rules should attach to."""

    return TechnicalDebtCategory.COMPLEXITY
