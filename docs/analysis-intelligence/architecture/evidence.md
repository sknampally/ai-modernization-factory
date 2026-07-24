# Architecture Evidence

## Sources

| Kind | Use |
| ---- | --- |
| `graph_edge` | Normalized dependency edges (cycles / direction / boundary) |
| `graph_node` | Coupling and concentration subjects |
| `symbol` | Framework leakage symbols |
| `enterprise_relationship` | Declared enterprise standard citations |

## Provenance labels

- `architecture_analysis_view` — observed from repository sources after normalization
- `enterprise-declared` — from optional Enterprise Knowledge Graph context

## Distinctions

| Class | Meaning |
| ----- | ------- |
| Observed | Import edges, symbols, package IDs |
| Derived | Primary units, layer labels, edge kinds, cycle identity |
| Declared | Allowed layer edges; configuration thresholds; unit-selection depth |
| Enterprise-declared | Standards labels when EKG present |

## Coverage (separated in 4.2.1a)

| Metric | Meaning |
| ------ | ------- |
| `extraction_coverage` | files_parsed / files_considered |
| `classification_coverage` | reliably layered primary units / primary units |
| `coverage_ratio` | alias of extraction_coverage (compat) |

Full extraction coverage does **not** imply high architectural-classification confidence.

## Language evidence providers (4.2.2)

Normalized language evidence (`SourceUnitEvidence`, `DependencyEvidence`,
`FrameworkUsageEvidence`) can feed `ArchitectureAnalysisView` when
`[evidence.language] enabled = true`. Providers collect facts; this view and the
shared rules still own architectural meaning and judgments. See
[../evidence-providers/README.md](../evidence-providers/README.md).

## Finding identity

`Finding.create` hash over rule ID + sorted subject keys. Cycle subjects use
canonical rotation-normalized **primary** unit sets. No timestamps or random UUIDs.

## Normalization attributes on edges

- `edge_kind`: runtime / type_only / registration / init_aggregation
- `raw_source_package` / `raw_target_package`
- `normalization`: included (excluded edges are dropped from the primary graph and counted)
