# Traceability

## Chain

```text
Executive Statement
  → Assessment Conclusion
  → Dimension / Subdimension (taxonomy node)
  → Finding IDs
  → Rule IDs + versions
  → Evidence (origin, strength, safe location)
  → Repository and/or Enterprise provenance
```

Also link:

- recommendation IDs
- score explanation IDs (future)
- confidence and coverage on the conclusion
- enterprise entity IDs when used (declared)

## Reader capabilities

A reader must be able to inspect:

- why a score was assigned
- why a risk was prioritized
- why a recommendation was proposed
- what evidence supports a statement
- what evidence was unavailable
- whether a claim is observed, derived, declared, inferred, or not assessed

## Implementation guidance (future)

- Prefer stable IDs already used by findings/recommendations.
- Appendices carry the dense tables; executive sections carry summaries with
  deep links or ID references.
- AI narratives must preserve this chain; they may paraphrase but not orphan
  claims.

## Current product

Today’s HTML report and JSON artifacts already reference findings and
recommendations. Full dimension-score explanations are methodology-only until
scoring is implemented.

## Architecture conclusions (Phase 4.2.3)

Optional conclusions reference source finding IDs and do not replace findings. Conclusion IDs are deterministic from policy, scope, and sorted source finding IDs.

Architecture assessment section edges (Phase 4.2.4) link section → pack → findings → evidence and section → conclusions → findings.
