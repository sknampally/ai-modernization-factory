# Graph building and linking

```text
Validated manifests
      │
      ▼
EnterpriseGraphBuilder  →  EnterpriseKnowledgeGraph
      │
      ▼
EnterpriseGraphLinker   →  assessment / finding / recommendation edges
      │
      ▼
EnterpriseGraphValidationService (final checks)
      │
      ▼
Persist complete graph only
```

## Builder rules

- Accepts typed validated inputs only (no filesystem / YAML)
- Deterministic entity and relationship ordering
- Duplicate-edge prevention
- Stable graph fingerprint from content
- Full rebuild is the supported Phase 3 path; selective rebuild interfaces exist
  for future use with explicit fallback

## Linker rules

Declared YAML relationships stay `declared_yaml`.

Derived links (assessment → finding impact, etc.) carry derivation provenance
and must not invent ownership or service mappings without a declared path.

## Persistence

JSON under the knowledge directory (`enterprise_graphs/`,
`enterprise_manifest_snapshots/`). Prior versions are immutable. Partial graphs
are never persisted.
