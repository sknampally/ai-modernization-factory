# Engineering knowledge store

**Status:** Phase 2B Increment 2 (snapshots, runs, immutable artifacts).

Assessment opens the store by default (`.aimf/knowledge/` via `[knowledge].directory`).

## Why SQLite + immutable JSON blobs

SQLite indexes repositories, snapshots, runs, and artifact metadata. Graph and
finding payloads remain content-addressed JSON under `blobs/` so schema-rich
graphs are not forced into relational tables and stay byte-inspectable.

## Layout

```text
.aimf/knowledge/
  knowledge.sqlite          # schema version 2
  locks/
  blobs/
    manifests/
    graphs/
    findings/
    recommendations/
    ai/
  tmp/
```

## Schema version 2

Adds:

- `repository_snapshots` — content fingerprint + manifest blob ref
- `assessment_runs` — running / completed / failed / aborted
- `knowledge_artifacts` — kind, schema version, blob ref/hash

Migration from v1 is transactional and preserves repositories/aliases.

## Repository identity vs snapshot identity

| Concept | Identity |
| ------- | -------- |
| Repository | Durable UUID + canonical key (Increment 1) |
| Snapshot | `(repository_id, branch_key, content_fingerprint)` |
| Assessment run | New UUID each execution; may reuse a snapshot |

Content fingerprint (not timestamps) decides snapshot reuse.

## Full recomputation

Increment 2 always runs the full deterministic pipeline. Fingerprints are stored
for future incremental work; they do not skip analysis yet.

## Persistence failure semantics

When knowledge persistence is enabled (default):

1. Reports may already be written under `reports/`.
2. If knowledge finalization fails, the assessment fails with a clear error.
3. The knowledge run is marked `failed`, never `completed`.
4. Incomplete runs are never returned by latest-completed queries.

## Recovery

On open, stale `running` rows older than six hours are marked `aborted`.
Temporary files under `tmp/` are cleaned. Corrupt blob hashes raise application
errors; they are not silently repaired.

## Git revision provenance

When `.git` is present, HEAD SHA is stored on the snapshot row. Dirty trees and
non-Git directories fall back safely. Snapshot content identity remains the
manifest fingerprint.

## Reports vs knowledge

Report retention (`keep=3`) does not delete knowledge store rows or blobs.
Knowledge retention policy is deferred.

## Legacy aliases

Conflicting optional `legacy_repository_key` aliases are skipped during
`register_or_resolve` and never merge distinct GitHub repositories. Explicit
`add_alias` still raises on conflict.

## Deferred

- MCP / query application services
- Incremental graph execution
- Knowledge retention / GC of unreferenced blobs
- Catalog-level EKG deduplication across repositories
