# Architecture

```
Architecture findings
  → FindingRelationshipBuilder
  → FindingClusterer
  → ConclusionPolicyRegistry / policies
  → ConclusionBuilder (per policy)
  → RecommendationConsolidator
  → ArchitectureConclusionResult
```

Does not bypass the Shared Rule Platform. Does not create findings.
