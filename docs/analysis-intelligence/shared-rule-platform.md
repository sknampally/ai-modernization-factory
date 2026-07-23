# Shared Rule Platform (Phase 4.1)

```text
Assessment Inputs
      │
      ▼
RuleExecutionContextFactory
      │
      ▼
Typed RuleExecutionContext
      │
      ▼
RuleRegistry → RulePlanner → RuleExecutor
      │
      ├─ applicability / suppression / evidence / telemetry
      ▼
RulePlatformExecutionResult → RuleFindingMapper → Finding
```

## Dual rule stacks (intentional)

| Stack | Package | Used by |
| ----- | ------- | ------- |
| Assessment Graph rules | `domain.rules.models.Rule` + `services.rule_engine` | `aimf assess` (unchanged) |
| Shared Rule Platform | `domain.rules.contracts.SharedRule` + `application.rules` | Phase 4.1+ packs (opt-in) |

## Identity

Rule IDs use `namespace.kebab-name` (example: `architecture.layer-dependency`).
No UUIDs. No class-name dependency.

Versions are `major.minor.patch` (`RuleVersion`).

Severity reuses `FindingSeverity`. Confidence is `RuleConfidence` (evidence certainty).

## Defaults

```toml
[rules]
enabled = false
fail_on_rule_error = false
max_rules_per_run = 1000
max_matches_per_rule = 1000
max_total_matches = 10000
max_evidence_per_match = 100
```

## CLI / MCP

- `aimf rules list|inspect|explain`
- MCP: `list_shared_rules`, `get_shared_rule`, `explain_shared_rule_metadata`,
  `get_shared_rule_platform_summary`

Fixture rules are never shown in production list/inspect output.
