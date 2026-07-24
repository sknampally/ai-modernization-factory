# Technical Debt Assessment Synthesis (Phase 4.3.5)

Deterministic themes, conclusions, and recommendations derived from the
Technical Debt assessment inventory and hotspots.

## Contract

| Input | Source |
| ----- | ------ |
| Production/test finding references | `all_finding_summaries` |
| Hotspots | `hotspot_inventory` |
| Coverage | `coverage` |
| Pack/section status | assessment gates |

Synthesis **does not** re-evaluate SharedRules or re-parse source.

| Output | Attached on section |
| ------ | ------------------- |
| Themes | `themes` / `theme_ids` |
| Concentration facts | `concentration_facts` |
| Conclusions | `conclusions` / `conclusion_ids` |
| Recommendations | `recommendations` / `recommendation_ids` |
| Bundle | `synthesis` |

Section schema: `assessment.technical_debt` @ `1.2.0`.

```toml
[assessment.sections.technical_debt]
enabled = true
include_synthesis = true
```

## Themes

One theme per complexity rule that has findings in a source role, keyed by
taxonomy `technical-debt.complexity` + rule ID.

## Concentration facts

Transparent counts/proportions only (not scores):

| Kind | Threshold for conclusion |
| ---- | ------------------------ |
| `package_share` | share ≥ **0.15** |
| `top10_hotspot_share` | share ≥ **0.40** |

Facts are always emitted for production packages/hotspots; conclusions fire
only when thresholds are met.

## Conclusion kinds

| Kind | Audience | Driver |
| ---- | -------- | ------ |
| `complexity_present` | production_health | production findings > 0 |
| `theme_complexity` | production_health | per production rule theme |
| `package_concentration` | production_health | package share ≥ 0.15 |
| `hotspot_concentration` | production_health | top-10 share ≥ 0.40 |
| `multi_rule_hotspots` | production_health | hotspot with ≥ 2 rules |
| `no_production_findings` | production_health | zero production findings |
| `partial_coverage` | coverage | complexity coverage partial |
| `test_maintainability` | test_observation | test findings > 0 |
| `disabled` | status | pack/section disabled |

Every conclusion references supporting theme IDs, finding IDs, and/or hotspot
IDs (or explicit empty production case).

## Recommendations

Every recommendation references ≥ 1 conclusion ID. Actions are factual and
conditional where appropriate (`If … is in scope…`). Effort/business impact
remain `unknown`.

## Production / test separation

- Production findings drive production-health conclusions.
- Test findings produce only `test_maintainability` (test_observation audience).
- Test observations must not be read as production-health defects.

## Traceability

Edges include `section_to_theme`, `section_to_conclusion`,
`section_to_recommendation`, `conclusion_to_finding`, `conclusion_to_theme`,
`conclusion_to_hotspot`, `recommendation_to_conclusion`.
