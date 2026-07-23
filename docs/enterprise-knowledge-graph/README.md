# Enterprise Knowledge Graph

Public product: **CodeStrata**. Internals remain `aimf`.

Phase 3 introduces an **enterprise-level** context above repositories. It is
distinct from the Engineering Knowledge Graph (technology concepts).

```text
Enterprise YAML
      │
      ▼
Load + Validate
      │
      ▼
Enterprise Graph Builder
      │
      ▼
Enterprise Knowledge Graph
      │
      ├─ Repository Registry
      ├─ Repository / Engineering / Assessment Graphs
      ├─ Findings
      └─ Recommendations
                       │
                       ▼
              Enterprise Impact Queries
```

## Principles

- YAML is declarative, human-readable, Git-friendly
- Safe YAML loading only (no code execution)
- Typed domain models; no graph database
- Declared vs derived provenance is explicit
- Enterprise metadata is **optional**; `aimf assess` unchanged
- Full assessment remains the default

## Quick start

```bash
aimf enterprise init enterprise --examples
aimf enterprise validate enterprise
aimf enterprise build enterprise
aimf enterprise query applications --domain student-services
aimf enterprise inspect application:student-information-system
```

## Configuration

```toml
[enterprise]
enabled = false
workspace = "enterprise"
schema_version = "codestrata.io/v1alpha1"
require_registered_repositories = true
allow_unresolved_repositories = false
```

## Package layout

- `aimf.domain.enterprise` — entities, relationships, identities
- `aimf.application.enterprise` — validate, build, link, query, persist ports
- `aimf.infrastructure.enterprise` — YAML loader, file graph store, workspace init
- CLI: `aimf enterprise …`
- MCP: twelve additive enterprise tools

## Docs in this folder

- [workspace.md](workspace.md) — YAML layout
- [entities.md](entities.md) — kinds and identity
- [relationships.md](relationships.md) — relationship model
- [schema-versioning.md](schema-versioning.md)
- [repository-resolution.md](repository-resolution.md)
- [graph-building.md](graph-building.md)
- [provenance.md](provenance.md)
- [validation.md](validation.md)
- [querying.md](querying.md)
- [incremental-rebuild.md](incremental-rebuild.md)
- [security.md](security.md)
- [cli.md](cli.md) / [mcp.md](mcp.md)
- [examples.md](examples.md)

## Non-goals (Phase 3)

- Analysis Intelligence rules (Phase 4)
- GitHub PR review (Phase 6)
- Graph databases, Cypher, SQL exposure
- Live cloud / CMDB / OpenAPI discovery
