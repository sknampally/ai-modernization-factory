# Analysis Intelligence

Phase 4 of CodeStrata.

| Milestone | Status |
| --------- | ------ |
| 4.1 Shared Rule Platform | Implemented (infrastructure) |
| 4.1.1 Rule Platform Integration Bridge | Complete |
| 4.1.2 CodeStrata Assessment Framework | Complete (methodology) |
| 4.2 Architecture Intelligence | Not started |
| 4.3 Technical Debt Intelligence | Not started |
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
