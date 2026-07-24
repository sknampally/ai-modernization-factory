# Architecture Recommendations

Every finding carries:

- action
- rationale
- expected engineering outcome
- effort band (`small` \| `medium` \| `large` \| `program` \| `unknown`)
- validation steps

Stored on `Finding.metadata` (`recommendation_*` keys) plus `remediation` text.

No dollar estimates, calendar estimates, staffing assumptions, or guaranteed
business outcomes.

Example (dependency cycle):

> Break the cycle using dependency inversion, a stable abstraction,
> responsibility realignment, interface extraction, an event boundary, or a
> shared neutral module. Regenerate the package dependency graph to validate
> removal.

## Conclusion-level consolidation (Phase 4.2.3)

When architecture conclusions are enabled, compatible finding-level recommendations may be
grouped under a consolidated recommendation. Original recommendations remain; groups cite
source recommendation and finding IDs. See
`docs/analysis-intelligence/architecture-conclusions/recommendations.md`.
