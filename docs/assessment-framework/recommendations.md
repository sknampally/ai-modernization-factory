# Recommendations

Findings describe **observed conditions**. Recommendations describe **potential
actions**.

## Hierarchy

| Level | Scope | Example |
| ----- | ----- | ------- |
| 1. Finding-level remediation | Single finding | Remove committed secret; rotate credentials |
| 2. Component-level improvement | Module/service | Extract shared library to break cycle |
| 3. Application-level initiative | One application | Upgrade Spring Boot to supported line |
| 4. Portfolio-level modernization | Multiple apps | Shared identity platform migration |
| 5. Governance / standards | Org policy | Adopt approved logging standard |

Community typically emits levels 1–3. Enterprise commonly adds 4–5 using
Enterprise Knowledge Graph context.

## Recommendation fields (methodology)

| Field | Notes |
| ----- | ----- |
| action | What to do |
| rationale | Why |
| expected outcome | What improves |
| affected scope | Files/modules/apps |
| dependencies | Blockers / prerequisites |
| estimated effort band | `small` \| `medium` \| `large` \| `program` \| `unknown` |
| urgency | Aligns with priority bands |
| confidence | Certainty of the recommendation |
| prerequisites | Required conditions |
| validation steps | How to verify |
| source findings | Finding IDs |
| enterprise context | Optional declared links |

## Effort bands

Use bands—not false precision:

- `small` — localized change
- `medium` — multi-file / multi-module
- `large` — cross-cutting refactor
- `program` — multi-team initiative
- `unknown` — insufficient basis

Do **not** produce dollar or calendar estimates without explicit user-supplied
cost/capacity models.

## Relationship to current product

Phase 3 recommendations already map from findings via the Recommendation Engine.
This hierarchy extends that model for CTO and portfolio narratives without
changing existing recommendation IDs in this milestone.

## Architecture recommendation consolidation (Phase 4.2.3)

Related architecture findings may produce a **consolidated recommendation group** while
preserving original finding-level recommendations. Groups coordinate actions; they do not
estimate cost or calendar duration.

Architecture recommendation groups may appear in the architecture assessment section without replacing finding-level recommendations (Phase 4.2.4).
When architecture report integration is enabled, consolidated groups are the primary recommendation presentation (Phase 4.2.5).
