# Evidence Provider Architecture

Application orchestration lives under `aimf.application.evidence.language`.
Domain contracts live under `aimf.domain.evidence.language`.

```
LanguageEvidenceContextFactory (service.build_context)
  → LanguageEvidenceProviderPlanner
  → LanguageEvidenceProviderExecutor
  → LanguageEvidenceAggregator
  → NormalizedLanguageEvidence (AggregatedLanguageEvidence)
  → ArchitectureAnalysisViewBuilder (architecture_adapter)
```

Legacy path (default):

```
paths + texts → collect_raw_package_facts → finalize_architecture_view
```

Provider path (opt-in):

```
providers → AggregatedLanguageEvidence → architecture_view_from_aggregated_evidence
```

Both paths share the same primary-unit collapse and dependency normalization
from Phase 4.2.1a.
