# Technical Debt Complexity Assessment (Phase 4.3.4)

Wires complexity evidence and `technical_debt.core` into `aimf assess`.

## Feature gates

```toml
[rules]
enabled = true

[rules.technical_debt]
enabled = true

[evidence.complexity]
enabled = true

[assessment.sections.technical_debt]
enabled = true
```

| Combination | Behavior |
| ----------- | -------- |
| Pack off, section on | `technical-debt-assessment.json` with status `disabled` |
| Pack on, complexity off | No evidence; no complexity matches; section may succeed empty/partial |
| Pack on, section off | Findings merge into `findings.json`; no TD section artifact |
| All on | Collect once, evaluate pack, assemble live section, write artifact |

## Pipeline

1. `evaluate_technical_debt_pack_detailed` (application/rules/technical_debt)
2. `ComplexityEvidenceService.collect` (when enabled)
3. Inject evidence into `RuleExecutionContext.complexity_evidence`
4. Register/evaluate pack → `RuleFindingMapper`
5. `TechnicalDebtAssessmentAssembler.assemble`
6. Write `technical-debt-assessment.json` when section enabled

Rules never re-parse source. Architecture assessment does not register
complexity collectors.

## Artifact

- Filename: `technical-debt-assessment.json`
- Section id: `assessment.technical_debt` @ `1.1.0`
- Includes finding references, **production-primary inventory**, test/unknown
  partitions, **source-unit hotspots**, coverage, limitations, execution
  summary, traceability — not conclusions, scores, or financial estimates

### Inventory fields (4.3.4A)

| Field | Meaning |
| ----- | ------- |
| `finding_ids` / `finding_summaries` | Primary inventory (production) |
| `all_finding_ids` / `all_finding_summaries` | Full traceability |
| `finding_inventory.production\|test\|unknown` | Role partitions + counts |
| `hotspot_inventory.production\|test\|unknown` | Deterministic source-unit groups |

### Status semantics (4.3.4A)

`partially_succeeded` requires **production** parse failures. Test/fixture
parse failures remain diagnostics (`files_parse_failed`) without degrading
section status. Unsupported languages and unavailable optional metrics are
limitations, not failures.

## Dogfood

See [PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md](../../reviews/PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md).
