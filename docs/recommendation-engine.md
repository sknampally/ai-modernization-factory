# Recommendation engine

Deterministic recommendations mapped from Phase 3 findings.

```text
findings.json
        ↓
Recommendation Engine (finding → action mappings)
        ↓
recommendations.json
```

## Guarantees

* Consumes findings and read-only graph context
* Never mutates Repository Graph, EKG, Assessment Graph, bindings, or findings
* Never calls AI
* Phase 3 `aimf.domain.recommendations.Recommendation` is distinct from Phase 1
  modernization recommendation DTOs and from AI enrichment narratives

## Artifact

`recommendations.json` in the run directory.

## Relationship to AI

Deterministic recommendations are the source of truth. Optional
[AI enrichment](ai-enrichment.md) may narrate them but must not create, delete,
or rewrite this artifact.

See also [architecture/recommendation-engine.md](architecture/recommendation-engine.md).
