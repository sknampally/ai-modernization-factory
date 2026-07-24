"""Map Shared Rule Platform matches onto existing Finding models."""

from __future__ import annotations

from aimf.domain.findings.enums import FindingCategory, FindingSeverity
from aimf.domain.findings.models import Finding, FindingEvidence
from aimf.domain.rules.enums import RuleCategory
from aimf.domain.rules.results import RuleMatch

_CATEGORY_MAP: dict[RuleCategory, FindingCategory] = {
    RuleCategory.ARCHITECTURE: FindingCategory.ARCHITECTURE,
    RuleCategory.TECHNICAL_DEBT: FindingCategory.TECHNICAL_DEBT,
    RuleCategory.SECURITY: FindingCategory.GOVERNANCE,
    RuleCategory.PERFORMANCE: FindingCategory.MODERNIZATION,
    RuleCategory.PLATFORM: FindingCategory.GOVERNANCE,
    RuleCategory.EXPERIMENTAL: FindingCategory.UNKNOWN,
}


class RuleFindingMapper:
    """Map validated matches to Phase 3 Finding models without altering ID scheme."""

    def map_match(self, match: RuleMatch, *, category: RuleCategory) -> Finding:
        evidence = tuple(
            FindingEvidence(
                evidence_type=item.kind.value,
                source_id=item.subject_reference,
                path=item.safe_location,
                excerpt=item.message or None,
            )
            for item in match.evidence
        )
        subjects = list(match.subject_keys) or list(match.affected_entities)
        if not subjects:
            subjects = [item.subject_reference for item in match.evidence]
        metadata: dict[str, str] = {
            "rule_version": str(match.rule_version),
            "confidence": match.confidence.value,
            "remediation": match.remediation or "",
            "provenance": match.provenance,
            "shared_rule_platform": "true",
            "business_impact": "unknown",
            "subject_keys": ",".join(str(item) for item in subjects),
        }
        if match.provenance == "architecture.core" or str(match.rule_id).startswith(
            "architecture."
        ):
            from aimf.application.rules.architecture.helpers import enrich_finding_metadata

            metadata.update(enrich_finding_metadata(str(match.rule_id)))
        elif match.provenance == "technical_debt.core" or str(match.rule_id).startswith(
            "technical_debt."
        ):
            from aimf.application.rules.technical_debt.helpers import (
                enrich_finding_metadata as enrich_debt_metadata,
            )

            metadata.update(enrich_debt_metadata(str(match.rule_id)))
            metadata.update(_technical_debt_evidence_metadata(match))
        return Finding.create(
            rule_id=str(match.rule_id),
            title=match.title,
            description=match.summary,
            severity=_map_severity(match.severity),
            category=_CATEGORY_MAP.get(category, FindingCategory.UNKNOWN),
            evidence=evidence,
            metadata=metadata,
            subject_keys=tuple(subjects),
        )

    def map_matches(
        self,
        matches: tuple[RuleMatch, ...],
        *,
        category_by_rule: dict[str, RuleCategory],
    ) -> tuple[Finding, ...]:
        findings = [
            self.map_match(
                match,
                category=category_by_rule.get(str(match.rule_id), RuleCategory.PLATFORM),
            )
            for match in matches
        ]
        return tuple(sorted(findings, key=lambda item: (item.rule_id, item.id, item.title)))


def _map_severity(severity: FindingSeverity) -> FindingSeverity:
    # RuleSeverity is an alias of FindingSeverity.
    return severity


_TD_EVIDENCE_METADATA_KEYS = (
    "metric",
    "value",
    "threshold",
    "severity_basis",
    "classification",
    "language",
    "callable_kind",
    "type_kind",
    "evidence_id",
)


def _technical_debt_evidence_metadata(match: RuleMatch) -> dict[str, str]:
    """Promote first-match complexity attributes for reviewable Finding metadata."""

    if not match.evidence:
        return {}
    attrs = match.evidence[0].attributes
    promoted: dict[str, str] = {}
    for key in _TD_EVIDENCE_METADATA_KEYS:
        value = attrs.get(key)
        if value:
            promoted[key] = value
    if match.evidence[0].line_start is not None:
        promoted["line_start"] = str(match.evidence[0].line_start)
    if match.evidence[0].line_end is not None:
        promoted["line_end"] = str(match.evidence[0].line_end)
    return promoted


def explain_finding_identity(match: RuleMatch) -> dict[str, str]:
    subjects = list(match.subject_keys) or list(match.affected_entities)
    if not subjects:
        subjects = [item.subject_reference for item in match.evidence]
    if not subjects:
        subjects = ["repository"]
    return {
        "scheme": "finding:{rule_id}:{sha256(sorted_subjects)[:16]}",
        "rule_id": str(match.rule_id),
        "subjects": ",".join(sorted(set(subjects))),
        "note": "Uses existing build_finding_id; timestamps and execution order are ignored",
    }