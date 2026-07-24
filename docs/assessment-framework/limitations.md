# Limitations

Static repository analysis **cannot reliably determine**:

- actual production performance or capacity
- production reliability / incident reality
- realized business value or revenue
- team productivity or culture
- true operational criticality (without declared enterprise metadata)
- exact modernization cost or duration
- actual exploitability of every potential weakness
- production data quality
- user satisfaction
- organization change readiness
- runtime behavior not represented in code
- undocumented external dependencies not present in the repository

## Recommended language

| Prefer | Avoid |
| ------ | ----- |
| “CodeStrata observed…” | “This system will fail…” |
| “The available evidence indicates…” | “This will cost $X…” |
| “This may increase…” | “The team is unproductive…” |
| “Enterprise metadata identifies…” | “The application cannot scale…” |
| “Runtime validation is recommended…” | “The system is secure…” |
| “This area was not assessed due to…” | Absolute guarantees without evidence |

## Product honesty

- Missing evidence → `unavailable` / `insufficient_evidence` / `not_assessed`
- No matched findings → do not claim excellence without positive evidence and coverage
- Enterprise criticality → declared, not proven by CodeStrata
- Current Engineering Assessment avoids fabricated composite health scores; future
  dimension scores must follow [scoring.md](scoring.md) and this limitations doc
