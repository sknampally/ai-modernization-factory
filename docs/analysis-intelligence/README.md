# Analysis Intelligence

Phase 4 of CodeStrata.

| Milestone | Status |
| --------- | ------ |
| 4.1 Shared Rule Platform | Implemented (infrastructure) |
| 4.1.1 Rule Platform Integration Bridge | Complete |
| 4.1.2 CodeStrata Assessment Framework | Complete (methodology) |
| 4.2 Architecture Intelligence | Complete (4.2.1–4.2.5) |
| 4.3 Technical Debt Intelligence | In Progress (4.3.1–4.3.3; assess/report not started) |
| 4.4 Security Intelligence | Not started |
| 4.5 Performance Intelligence | Not started |
| 4.6 Modernization Intelligence | Not started |

## Phase 4.1

The Shared Rule Platform provides deterministic rule identity, registration,
planning, execution, evidence, suppression, finding mapping, telemetry, and
explainability. It is **disabled by default** and **not wired into**
`aimf assess`.

Production Assessment Graph rules continue to use the existing
`services/rule_engine.RuleEngine` path.

See [shared-rule-platform.md](shared-rule-platform.md).

## Phase 4.1.1

Compatibility bridge between legacy `RuleEngine` and the Shared Rule Platform:

- `LegacyRuleAdapter`
- `RuleExecutionFacade`
- Finding-preserving `evaluate_adapted`

Assessment behaviour is unchanged. See
[rule-platform-migration.md](rule-platform-migration.md).

## Phase 4.1.2

Assessment methodology for dimensions, taxonomy, evidence, confidence, scoring
design, prioritization, and CTO report structure. No production rules or scoring
wired into assessment. See
[../assessment-framework/README.md](../assessment-framework/README.md).

## Phase 4.2.1

Initial Architecture Intelligence pack `architecture.core` (7 production SharedRules).
Discoverable via CLI/MCP; merged into `aimf assess` only when
`[rules] enabled` and `[rules.architecture] enabled`. See
[architecture/README.md](architecture/README.md).

## Phase 4.2.2

Language Evidence Provider Foundation: normalized providers collect facts;
shared architecture rules remain language-independent. Pipeline disabled by
default. See [evidence-providers/README.md](evidence-providers/README.md).

## Phase 4.2.4

Architecture assessment section integration. See [architecture-assessment/README.md](architecture-assessment/README.md).

## Phase 4.2.5

Architecture CTO report integration: assessment section → report adapter →
`report.json` / HTML. See [architecture-reporting/README.md](architecture-reporting/README.md).

## Phase 4.3.1

Technical Debt domain foundation: taxonomy, assessment section contracts,
feature gates, empty/disabled sections. No production debt rules yet. See
[technical-debt/README.md](technical-debt/README.md) and
[../design/PHASE_4_3_TECHNICAL_DEBT_INTELLIGENCE.md](../design/PHASE_4_3_TECHNICAL_DEBT_INTELLIGENCE.md).

## Phase 4.3.2

Complexity evidence collectors (Language Evidence Platform): Python `ast` and
Java structural scan. Explicit metric availability; `.aimf` excluded. See
[technical-debt/complexity-evidence.md](technical-debt/complexity-evidence.md).

## Phase 4.3.3

Technical Debt complexity SharedRules (`technical_debt.core`) consume complexity
evidence and emit deterministic findings. See
[technical-debt/complexity-rules.md](technical-debt/complexity-rules.md).

## Phase 4.3.4

Technical Debt complexity assessment vertical: assess orchestration, feature
gates, section artifact, and dogfood review. See
[technical-debt/complexity-assessment.md](technical-debt/complexity-assessment.md)
and
[../reviews/PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md](../reviews/PHASE_4_3_COMPLEXITY_DOGFOOD_REVIEW.md).
