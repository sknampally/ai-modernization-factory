# Technical Debt Complexity Rules (Phase 4.3.3)

SharedRules in pack `technical_debt.core` that evaluate Language Evidence
complexity facts.

## Rules

| Rule ID | Subject | Metric | Default threshold |
| ------- | ------- | ------ | ----------------- |
| `technical_debt.large-callable` | callable | physical lines | 50 |
| `technical_debt.excessive-branching` | callable | branch points | 10 |
| `technical_debt.deep-nesting` | callable | max nesting depth | 4 |
| `technical_debt.excessive-parameters` | callable | parameter count | 5 |
| `technical_debt.oversized-type` | type/module | physical lines | 300 |

Findings emit only when the metric is **available** and the value is **strictly
greater** than the threshold.

## Configuration

```toml
[rules]
enabled = true

[rules.technical_debt]
enabled = true

[rules.technical_debt.complexity.large_callable]
max_physical_lines = 50
```

## Limitations

- No conclusions, scoring, or CTO report debt section yet (4.3.5–4.3.6).
- Cognitive complexity and duplication are out of scope.
- JS/TS complexity collectors are unsupported.
- Python method/constructor parameter counts exclude `self` / `cls`.
- HIGH severity requires `value > 2 × threshold` (documented `severity_basis`).

Assess wiring: [complexity-assessment.md](complexity-assessment.md).
