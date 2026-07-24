# Technical Debt Intelligence

Phase 4.3 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.3.1 Domain Foundation | Complete |
| 4.3.2 Complexity Evidence | Complete |
| 4.3.3 Complexity Rules & Findings | Complete |
| 4.3.4 Complexity Assessment Vertical and Dogfood | Complete |
| 4.3.4A Complexity Precision and Inventory Usability | Complete |
| 4.3.5 Assessment Synthesis | Complete |
| 4.3.6 Report Integration | Complete |

Design authority:
[PHASE_4_3_TECHNICAL_DEBT_INTELLIGENCE.md](../../design/PHASE_4_3_TECHNICAL_DEBT_INTELLIGENCE.md).

Dogfood review:
[PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md](../../reviews/PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md).

Acceptance review:
[PHASE_4_3_ACCEPTANCE_REVIEW.md](../../reviews/PHASE_4_3_ACCEPTANCE_REVIEW.md).

CTO report integration:
[technical-debt-reporting/README.md](../technical-debt-reporting/README.md).

## 4.3.1 Foundation

- Taxonomy: `TechnicalDebtCategory`
- Assessment section: `assessment.technical_debt` @ `1.0.0`
- Pack reserved: `technical_debt.core` @ `1.0.0`
- Feature gates default **disabled**
- Shared `Finding` reused; `FindingCategory.TECHNICAL_DEBT` added

```toml
[rules.technical_debt]
enabled = false

[assessment.sections.technical_debt]
enabled = false
```

## 4.3.2 Complexity Evidence

- Owned by **Language Evidence Platform** (`domain/evidence/language/complexity`)
- Collectors: Python (`ast`), Java (structural scan)
- Metrics: physical lines, parameters, branch points, nesting depth, callable
  counts, class/module size
- Explicit `IntMetric.availability` (never encode unsupported as zero)
- Default exclusions include `.aimf/` workspace clones
- Thin TD projection only

```toml
[evidence.complexity]
enabled = true
```

See also: [complexity-evidence.md](complexity-evidence.md).

## 4.3.3 Complexity Rules & Findings

- Pack: `technical_debt.core` with five complexity SharedRules
- Consumes complexity evidence only (no re-parse)
- Thresholds under `[rules.technical_debt.complexity.*]`
- HIGH severity only when `value > 2 × threshold`

See: [complexity-rules.md](complexity-rules.md), [rule-pack.md](rule-pack.md).

## 4.3.4 Complexity Assessment Vertical and Dogfood

- Assess orchestration respects complexity, pack, and section gates
- Collects evidence once → rule context → findings → section artifact
- Disabled/empty behavior preserved explicitly
- Complexity collectors are not registered with Architecture assessment
- Dogfood: CodeStrata root + spring-petclinic Java reference

### 4.3.4A Inventory usability

- Production / test / unknown finding partitions
- Primary section inventory is production by default
- Deterministic source-unit hotspots (no composite score)
- Test/fixture parse failures do not force `partially_succeeded`

See: [complexity-assessment.md](complexity-assessment.md),
[PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md](../../reviews/PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md).

## 4.3.5 Assessment Synthesis

Deterministic themes, concentration facts, conclusions, and recommendations
from the production-primary inventory and hotspots. Test findings produce a
separate test-maintainability observation only.

See: [synthesis.md](synthesis.md).
