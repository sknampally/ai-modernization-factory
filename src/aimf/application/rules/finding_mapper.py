"""Map Shared Rule Platform matches onto existing Finding models."""

from __future__ import annotations

from aimf.domain.findings.enums import FindingCategory, FindingSeverity
from aimf.domain.findings.models import Finding, FindingEvidence
from aimf.domain.rules.enums import RuleCategory
from aimf.domain.rules.results import RuleMatch

_CATEGORY_MAP: dict[RuleCategory, FindingCategory] = {
    RuleCategory.ARCHITECTURE: FindingCategory.ARCHITECTURE,
    RuleCategory.TECHNICAL_DEBT: FindingCategory.MAINTAINABILITY,
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
                excerpt=None,
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