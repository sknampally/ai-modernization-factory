# Phase 4.3 — Technical Debt Intelligence

## Status

| Sub-milestone | Status |
| ------------- | ------ |
| 4.3.1 Technical Debt Domain Foundation | Implemented |
| 4.3.2 Complexity Evidence | Implemented |
| 4.3.3 Initial Debt Rule Pack (Complexity Rules) | Implemented |
| 4.3.4 Complexity Assessment Vertical and Dogfood | Implemented |
| 4.3.4A Complexity Precision and Inventory Usability | Implemented |
| 4.3.5 Debt Conclusions and Aggregation (Assessment Synthesis) | Implemented |
| 4.3.6 Debt Report Integration | Implemented |

## Goals

Provide deterministic, evidence-backed technical debt analysis that:

- reuses the Shared Rule Platform and shared `Finding` model
- keeps Architecture Intelligence behavior unchanged
- never invents financial cost, engineering hours, productivity loss,
  modernization percentage, business impact, or remediation priority via AI
- remains disabled by default until explicitly enabled

## Design decisions (4.3.1)

### 1. Shared Finding model — reuse with an additive category

**Decision:** Continue using the shared Phase 3 `Finding` model for future debt
findings.

**Changes:**

- Add `FindingCategory.TECHNICAL_DEBT = "technical_debt"`
- Map `RuleCategory.TECHNICAL_DEBT` → `FindingCategory.TECHNICAL_DEBT`
  (previously mapped to `MAINTAINABILITY`)

**Rationale:** Debt findings need the same identity, evidence, severity, and
traceability contracts as architecture findings. A parallel finding type would
duplicate serialization, MCP, and report plumbing without improving type safety.
Debt-specific meaning lives in:

- `rule_id` namespace `technical_debt.*`
- taxonomy metadata (`technical-debt.*`)
- assessment-section projection (`TechnicalDebtFindingReference`)

### 2. No universal IntelligencePack abstraction

**Decision:** Do not introduce a generic pack plugin framework in 4.3.1.

Mirror Architecture Intelligence packages under `domain/technical_debt/` and
`application/technical_debt/` until a second independent pack proves duplication
pain.

### 3. Assessment section reserved early; empty by design

**Decision:** Introduce `assessment.technical_debt` section contracts now so
later rule packs have a stable artifact/schema target.

Phase 4.3.1 produces only:

- `disabled` sections (feature gate off)
- `succeeded` empty sections (gate on, no rules registered yet)

No production rules, conclusions, recommendations, scoring, or report narrative.

### 4. Forbidden precision fields

The assessment model **must not** include:

- financial cost / interest / dollar estimates
- engineering hours / staffing / calendar duration
- productivity loss percentages
- modernization completion percentages
- inferred business impact (always `unknown` unless enterprise context later)

Limitations explicitly document these absences.

### 5. Feature gates (all default false)

```toml
[rules]
enabled = false

[rules.technical_debt]
enabled = false

[assessment.sections.technical_debt]
enabled = false
```

Enabling assessment section does **not** auto-enable rules. Enabling rules does
not auto-write the assessment artifact until assess orchestration is wired in a
later milestone.

### 6. Identity contract

| Entity | ID pattern |
| ------ | ---------- |
| Section | `assessment.technical_debt` @ `1.0.0` |
| Pack (reserved) | `technical_debt.core` @ `1.0.0` |
| Rule IDs (future) | `technical_debt.<kebab-name>` |
| Taxonomy | `technical-debt.<kebab-leaf>` |
| Limitations | `td-limitation:<sha12>` |
| Trace edges | `td-trace:<sha16>` |
| Findings | existing `Finding` / `build_finding_id` |

Identical inputs must yield identical fingerprints, limitation IDs, and
ordering.

### 7. Workspace / generated content

Architecture precision corrections established exclusion of `.aimf` workspace
content from analysis inputs. Technical Debt Intelligence must preserve those
exclusions; tests and generated workspace clones must never become debt
evidence.

## Package layout (4.3.1)

```
src/aimf/domain/technical_debt/
  ids.py
  taxonomy.py
  assessment/
    enums.py
    identifiers.py
    models.py

src/aimf/application/technical_debt/
  assessment/
    assembler.py
    factory.py
    artifacts.py
```

Artifact filename: `technical-debt-assessment.json`

## Design decisions (4.3.2) — Complexity Evidence

### 1. Evidence ownership — Language Evidence Platform

**Decision:** Structural complexity facts are owned by the Language Evidence
Platform under `domain/evidence/language/complexity/` and
`application/evidence/language/complexity/`.

Technical Debt does **not** own parsers. It may consume a thin projection
(`application/technical_debt/evidence/complexity_projection.py`) when rules
are added later.

**Rationale:** Complexity metrics are reusable syntactic facts (also useful
beyond debt). Duplicating Java/Python extraction under Technical Debt would
violate the “evidence describes facts; rules interpret debt” boundary.

### 2. No Architecture pipeline coupling

Complexity collectors are **not** registered in
`create_language_evidence_registry` and are **not** invoked by Architecture
Intelligence assessment. Existing architecture/language-evidence behavior is
unchanged.

### 3. Parsers used

| Language | Mechanism | Notes |
| -------- | --------- | ----- |
| Python | stdlib `ast` | Credible structural metrics |
| Java | brace-aware structural scan | Comments/strings scrubbed; lambdas not extracted |
| JavaScript/TypeScript | Unsupported | No credible parser in-tree |

### 4. Metric availability

Every integer metric uses `IntMetric(availability, value)`. Unsupported or
failed metrics leave `value=None`. Measured zeros remain `AVAILABLE` with
`value=0`.

### 5. Workspace exclusion

Default complexity ignore markers include `/.aimf/` (and vendor/generated/
build outputs). Relative paths under `.aimf/` are never measured.

### Metric support matrix (4.3.2)

| Metric | Python | Java | JS/TS |
| ------ | ------ | ---- | ----- |
| Physical line count (file) | available | available | unsupported |
| Physical line count (callable) | available | available | unsupported |
| Parameter count | available | available | unsupported |
| Branch-point count | available | available | unsupported |
| Max nesting depth | available | available | unsupported |
| Callable count (class/module) | available | available | unsupported |
| Class/module size (physical lines) | available | available | unsupported |
| Cognitive complexity | unsupported | unsupported | unsupported |
| Cyclomatic complexity (exact) | unsupported (branch points only) | unsupported (branch points only) | unsupported |

### Package layout (4.3.2)

```
src/aimf/domain/evidence/language/complexity/
  enums.py
  identifiers.py
  models.py

src/aimf/application/evidence/language/complexity/
  paths.py
  python_extractor.py
  java_extractor.py
  collector.py
  service.py
  artifacts.py

src/aimf/application/technical_debt/evidence/
  complexity_projection.py
```

Optional artifact: `complexity-evidence.json`

## Intentionally not implemented in 4.3.1

- complexity / duplication / size analyzers
- code-smell detection rules
- dependency support-window rules
- debt conclusions or recommendation groups
- scoring / grades / prioritization engines
- AI narrative
- HTML / report.json debt section
- assess orchestration wiring to emit the artifact on every run
- MCP / CLI debt inspection commands (optional later)

## Intentionally not implemented in 4.3.2

- debt rules / findings / severity / confidence
- thresholds or hotspot prioritization
- cognitive complexity
- duplication detection / maintainability indexes
- hotspot prioritization
- conclusions, recommendations, scoring
- JSON/HTML CTO report debt or complexity sections
- CLI / MCP complexity commands
- wiring complexity collection into `aimf assess`
- generic IntelligencePack abstraction
- JavaScript/TypeScript complexity

## Design decisions (4.3.3) — Complexity Rules & Findings

### 1. Shared Rule Platform pack `technical_debt.core`

Five deterministic SharedRules consume `AggregatedComplexityEvidence` via
`RuleExecutionContext.complexity_evidence`. They never re-parse source.

| Rule ID | Metric | Default threshold (strict `>`) |
| ------- | ------ | ------------------------------ |
| `technical_debt.large-callable` | callable `physical_line_count` | 50 |
| `technical_debt.excessive-branching` | `branch_point_count` | 10 |
| `technical_debt.deep-nesting` | `max_nesting_depth` | 4 |
| `technical_debt.excessive-parameters` | `parameter_count` | 5 |
| `technical_debt.oversized-type` | type/module `physical_line_count` | 300 |

Unsupported / unavailable metrics never produce findings.

### 2. Configuration

```toml
[rules.technical_debt]
enabled = false

[rules.technical_debt.complexity]
enabled = true

[rules.technical_debt.complexity.large_callable]
max_physical_lines = 50
```

Pack discovery is registered for CLI/MCP. Assess synthesis is delivered in
4.3.4 (assessment vertical).

### 3. Findings

Matches map to `FindingCategory.TECHNICAL_DEBT` with stable IDs, HIGH
confidence when metrics are available, severity MEDIUM (HIGH when value >
2× threshold), source location from complexity spans, and concise remediation
text.

## Intentionally not implemented in 4.3.3

- assessment synthesis / section population from live rules
- conclusions, recommendation groups, scoring, prioritization
- report JSON/HTML integration
- CLI/MCP debt-specific commands beyond Shared Rule discovery
- duplication / smell / dependency-support rules
- IntelligencePack abstraction
- wiring complexity collection into every `aimf assess` run

## Design decisions (4.3.4) — Complexity Assessment Vertical and Dogfood

### 1. Assess orchestration

When `[rules] enabled` and `[rules.technical_debt] enabled`:

1. Collect complexity evidence once (if `[evidence.complexity] enabled`)
2. Inject `AggregatedComplexityEvidence` into Shared Rule context
3. Evaluate `technical_debt.core` (no source re-parse in rules)
4. Map matches through `RuleFindingMapper` into shared `Finding`s
5. Merge into the assess finding set

When `[assessment.sections.technical_debt] enabled`, assemble
`TechnicalDebtAssessmentSection` and write `technical-debt-assessment.json`.
Section-on / pack-off emits an explicit `disabled` section.

### 2. Feature-gate contract

| Gate | Collect evidence | Evaluate pack | Write section artifact |
| ---- | ---------------- | ------------- | ---------------------- |
| rules + technical_debt | if complexity enabled | yes | only if section enabled |
| complexity disabled | no | yes (no matches) | if section enabled |
| section disabled | per above | per above | no |
| pack disabled + section enabled | no | no | disabled section |

### 3. Severity HIGH basis

HIGH requires `value > 2 × threshold` (`SEVERITY_HIGH_MULTIPLIER = 2`), recorded
as `severity_basis` on finding metadata. Basic threshold crossings stay MEDIUM.

### 4. Parameter-count credibility

Python method/constructor parameter counts exclude implicit `self` / `cls`.

### 5. Dogfood

See [PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md](../reviews/PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md).

## Design decisions (4.3.4A) — Inventory usability

### 1. Production-primary inventory

`finding_ids` / `finding_summaries` are production-only. Full traceability is
retained via `all_finding_*` and `finding_inventory.test|unknown`.

### 2. Deterministic hotspots

Source-unit hotspots group overlapping rules without inventing a composite
score or priority. Ordering is severity → count → path → unit → id.

### 3. Status semantics

`partially_succeeded` requires material **production** parse failures.
Test/fixture parse failures stay in diagnostics (`files_parse_failed`) and do
not degrade section status. Unsupported languages and unavailable optional
metrics remain limitations, not failures.

## Intentionally not implemented in 4.3.4 / 4.3.4A

- conclusions / aggregation / debt themes (later: 4.3.5)
- scoring, ratings, hotspot prioritization formulas
- financial / effort / velocity / business-impact estimates
- CTO report JSON/HTML debt section (later: 4.3.6)
- duplication or smell rules
- CLI/MCP debt-specific commands
- generic IntelligencePack abstraction
- JS/TS or cognitive complexity

## Next milestones (preview)

1. **4.4** Security Intelligence (separate phase)

## Design decisions (4.3.6) — CTO Report Integration

### 1. Presentation adapter only

`TechnicalDebtReportAdapter` maps an in-memory `TechnicalDebtAssessmentSection`
to `TechnicalDebtReportSection`. It does not collect evidence, evaluate rules,
re-read artifacts, or generate AI inference.

### 2. Additive report schema

`report.json` schema remains `1.2`. When
`[report.sections.technical_debt] enabled = true` and an assessment section is
available, `assessment.technical_debt` is added. When disabled or unavailable,
the key is omitted (backward compatible).

### 3. Production vs test in the customer report

Production metrics, themes, hotspots, conclusions, and recommendations are
primary. Test findings appear only under a separate test-maintainability
observation. Hotspot order is inventory presentation order, not a priority score.

See [technical-debt-reporting/README.md](../analysis-intelligence/technical-debt-reporting/README.md).

## Design decisions (4.3.5) — Assessment Synthesis

### 1. Inventory-driven only

Synthesis consumes assessment finding references, hotspots, and coverage. It
does not re-run rules or parse source.

### 2. Bounded conclusion kinds

Themes derive from taxonomy + rule IDs. Concentration uses transparent share
thresholds (package ≥ 15%, top-10 hotspots ≥ 40%). Conclusions use fixed
templates; recommendations always cite conclusion IDs and remain conditional
where appropriate.

### 3. Production vs test

Production findings drive production-health conclusions. Test findings emit a
separate `test_maintainability` observation that must not be treated as
production-health evidence.

See [synthesis.md](../analysis-intelligence/technical-debt/synthesis.md).

## Package layout (4.3.3–4.3.4)

```
src/aimf/application/rules/technical_debt/
  assessment.py          # assess orchestration (4.3.4)
  pack.py
  registration.py
  rules.py
  helpers.py
  recommendations.py

src/aimf/application/technical_debt/assessment/
  assembler.py           # live/disabled/empty section assembly
  artifacts.py
  factory.py

src/aimf/domain/technical_debt/ids.py   # RULE_* constants
```

## Compatibility

- Architecture Intelligence packages and defaults remain unchanged
- Report schema remains additive (`assessment.technical_debt` optional under 1.2)
- Existing findings continue to deserialize; new category is optional
- Complexity collectors remain outside Architecture assessment registration