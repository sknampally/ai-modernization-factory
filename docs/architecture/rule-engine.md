"""Assessment Graph Rule Engine (Phase 3).

```text
Repository Graph
        ↓
Assessment Graph (+ inventory / bindings)
        ↓
Rule Engine (deterministic builtin rules)
        ↓
Findings (findings.json)
        ↓
Recommendation Engine
        ↓
Recommendations (recommendations.json)
        ↓
optional AI / reporting
```

Rules evaluate a read-only ``RuleContext`` and never mutate Repository Graph,
Engineering Knowledge Graph, or Assessment Graph. They never call AI.

Phase 3 ``aimf.domain.findings.Finding`` is distinct from Phase 1
``aimf.models.Finding`` (UUID-based analyzer findings).

See also ``docs/architecture/recommendation-engine.md``.
