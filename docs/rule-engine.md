# Rule engine

Deterministic findings from Assessment Graph context.

```text
Assessment Graph (+ inventory / bindings)
        ↓
Rule Engine (builtin rules)
        ↓
findings.json
```

## Guarantees

* Read-only evaluation (`RuleContext`); no graph mutation
* No AI provider calls
* Stable finding IDs suitable for recommendation mapping and enrichment
  traceability
* Phase 3 `aimf.domain.findings.Finding` is distinct from Phase 1
  `aimf.models.Finding` (UUID-based analyzer findings)

## Artifact

`findings.json` in the run directory.

## Downstream

Findings feed the [Recommendation Engine](recommendation-engine.md). Optional
[AI enrichment](ai-enrichment.md) may reference finding IDs but must not alter
this file.

See also [architecture/rule-engine.md](architecture/rule-engine.md).
