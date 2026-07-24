# Architecture Severity

Uses existing `FindingSeverity` / `RuleSeverity` (no parallel enum).

| Rule | Logic |
| ---- | ----- |
| dependency-cycle | medium if cycle size ≤ 2; else high |
| invalid-dependency-direction | medium |
| layer-boundary-violation | high |
| excessive-cross-module-coupling | medium; high if count ≥ 2× threshold |
| component-concentration | medium; high if share ≥ 0.50 |
| framework-leakage | medium |
| enterprise-standard-mismatch | high |

Critical is reserved for future exceptional, explicitly documented conditions.

## Business impact

Repository-only assessments set `business_impact = unknown`. Technical severity
never auto-promotes business impact.
