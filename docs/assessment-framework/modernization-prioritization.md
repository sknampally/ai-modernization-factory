# Modernization Prioritization

## Sequence

```text
Finding
  → Recommendation
  → Initiative Candidate
  → Dependency Analysis
  → Priority
  → Modernization Wave
```

Waves are **dependency-driven**, not mere severity buckets.

## Suggested waves

### Wave 0 — Validate and Stabilize

- Confirm uncertain critical findings
- Close severe security exposures
- Establish missing inventory or observability foundations

### Wave 1 — Quick Wins and Risk Reduction

- Supported dependency upgrades
- Configuration corrections
- Straightforward architectural corrections

### Wave 2 — Foundation Modernization

- Modularization
- Platform upgrades
- Test foundations
- Deployment foundations
- Data-access separation

### Wave 3 — Structural Modernization

- Service decomposition
- Data modernization
- Integration redesign
- Cloud-native enablement

### Wave 4 — Strategic Enablement

- AI enablement
- Platform productization
- Advanced automation
- Portfolio optimization

## Repository-only vs enterprise

| Mode | Inputs |
| ---- | ------ |
| Repository-only | Technical severity, confidence, dependency centrality in-repo, effort bands |
| Enterprise-enhanced | + criticality, capabilities, ownership, initiatives, cross-repo deps, standards |

## Initiative candidates

Group related recommendations when they share:

- the same application or capability
- the same platform upgrade
- the same architectural boundary
- the same enterprise initiative ID (declared)

Do not invent budgets, savings, or completion forecasts.

## Architecture conclusions → waves (Phase 4.2.3)

Architecture conclusions typically map to Wave 0 (insufficient evidence), Wave 2
(boundary/dependency foundation cleanup), or Wave 3 (structural decomposition) per
documented conclusion policy—not by severity alone.
