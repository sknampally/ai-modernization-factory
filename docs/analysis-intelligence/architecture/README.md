# Architecture Intelligence

Phase 4.2 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.2.1 Initial Architecture Rule Pack | Complete |
| 4.2.1a Architecture Rule Precision Hardening | Complete |
| 4.2.2 Language Evidence Provider Foundation | Complete |
| 4.2.3 Architecture Conclusions and Aggregation | Complete |
| 4.2.4 Architecture Assessment Integration | Complete |
| 4.2.5 CTO Report Integration | Implemented; Phase 4.2 acceptance blocked on precision correction |

## Pack

- **ID:** `architecture.core`
- **Version:** `1.0.0`
- **Default:** disabled (`[rules.architecture] enabled = false`)
- **Execution path:** `RuleExecutionFacade` → Shared Rule Platform → `RuleFindingMapper` → `Finding`

## Documents

- [rule-pack.md](rule-pack.md) — pack contract
- [rules.md](rules.md) — per-rule specification
- [configuration.md](configuration.md) — settings
- [evidence.md](evidence.md) — evidence model
- [severity.md](severity.md) — severity logic
- [recommendations.md](recommendations.md) — remediation guidance
- [limitations.md](limitations.md) — known gaps
- [examples.md](examples.md) — worked examples
- [migration.md](migration.md) — compatibility notes

Language evidence providers (Phase 4.2.2): see
[../evidence-providers/README.md](../evidence-providers/README.md).

Architecture conclusions (Phase 4.2.3): see
[../architecture-conclusions/README.md](../architecture-conclusions/README.md).

## Enablement

```toml
[rules]
enabled = true

[rules.architecture]
enabled = true
```

When disabled (default), `aimf assess` behaviour is unchanged.

Phase 4.2.4: [Architecture Assessment Integration](../architecture-assessment/README.md).

Phase 4.2.5: [Architecture CTO Report Integration](../architecture-reporting/README.md).
