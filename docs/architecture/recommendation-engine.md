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
optional AI / reporting (separate; not fed full recommendations JSON yet)
```

The Recommendation Engine consumes Phase 3 findings and read-only graph
context. It never mutates Repository Graph, Engineering Knowledge Graph,
Assessment Graph, bindings, or findings. It never calls AI.

Phase 3 ``aimf.domain.recommendations.Recommendation`` is distinct from:

- Phase 1 ``aimf.models`` / ``ModernizationRecommendationEngine`` outputs
- AI ``aimf.ai.recommendations`` narratives produced under ``--with-ai``

Deterministic recommendations are implemented now. Future AI-enriched
prioritization or narrative remains optional and separate.
