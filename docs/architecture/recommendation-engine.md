"""Assessment Graph Recommendation Engine (Phase 3).

```text
Repository Graph
        ↓
Assessment Graph (+ inventory / bindings)
        ↓
Rule Engine
        ↓
Findings (findings.json)
        ↓
Recommendation Engine (deterministic finding → action mappings)
        ↓
Recommendations (recommendations.json)
        ↓
optional AI enrichment (ai-enrichment.json; one provider call)
```

The Recommendation Engine consumes Phase 3 findings and read-only graph
context. It never mutates Repository Graph, Engineering Knowledge Graph,
Assessment Graph, bindings, or findings. It never calls AI.

Phase 3 ``aimf.domain.recommendations.Recommendation`` is distinct from:

- Phase 1 ``aimf.models`` / ``ModernizationRecommendationEngine`` outputs
- AI enrichment narratives in ``aimf.domain.ai_enrichment`` / ``ai-enrichment.json``
- Legacy Phase 1 report contract ``aimf.ai.recommendations`` (bridged for HTML/JSON)

Deterministic recommendations remain the source of truth. AI enrichment is
optional, interpretive only, and must not modify ``recommendations.json``.
See ``docs/architecture/ai-enrichment.md``.
