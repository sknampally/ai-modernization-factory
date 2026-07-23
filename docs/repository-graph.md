# Repository graph

AIMF builds a deterministic structural view of the assessed repository.

## Pipeline

```text
Repository (scan)
     ↓
Repository Inventory (manifest + fingerprints)
     ↓
Repository Graph (nodes + relationships)
     ↓
Dependency extraction (Maven / package.json)
```

## What it contains

* Repository, module, and file structure
* Dependency nodes with versions where known (version is a property, not part of
  the dependency identity)
* Highlights such as Java language level, Spring Boot version, and Node engine
  when detectable from manifests

## What it excludes

* Full source file bodies
* Secrets and absolute host paths in customer-facing reports
* Lockfile-only resolution (v0.1.0 uses manifest-declared versions)

## Artifacts

Under `reports/<repo>/<run>/graphs/`:

* `repository-manifest.json`
* `repository-graph.json`
* `graph-summary.json` (plus knowledge/assessment siblings)

## Boundaries

* Phase 1 `Repository` / `RepositoryFacts` remain scanner and analyzer DTOs.
* The Repository Graph is adapted from inventory; it is not collapsed into Phase 1 models.
* Graph construction never calls AI.

See also [runtime.md](runtime.md) and [assessment-graph.md](assessment-graph.md).
