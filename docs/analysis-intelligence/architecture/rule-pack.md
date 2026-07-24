# Architecture Rule Pack (`architecture.core`)

| Field | Value |
| ----- | ----- |
| Pack ID | `architecture.core` |
| Version | `1.0.0` |
| Title | Architecture Intelligence Core |
| Category | `architecture` |
| Default enabled | `false` |
| Languages | Java, Python, JavaScript, TypeScript (via source import extraction) |
| Documentation | this directory |
| Precision | Phase **4.2.1a** unit selection + dependency normalization |

## Included rules (7)

1. `architecture.dependency-cycle`
2. `architecture.invalid-dependency-direction`
3. `architecture.layer-boundary-violation`
4. `architecture.excessive-cross-module-coupling`
5. `architecture.component-concentration`
6. `architecture.framework-leakage`
7. `architecture.enterprise-standard-mismatch` (enterprise context required)

## Deferred

- `architecture.service-dependency-cycle` — no distinct higher-level service graph yet.

## Architectural-unit selection

Primary subjects are **not** every nested package. Policy:

1. Declared / build modules (when available later)
2. Validated architectural components (when available later)
3. **Top-level source packages** with layer-marker awareness
4. Nested packages retained only as evidence (`collapsed_packages`)

Reverse-DNS packages (`com.*` / `org.*`) use depth ≥ 3 so sibling modules stay distinct.

## Dependency normalization

Before rules run, the view:

- collapses nested packages into primary units
- excludes parent/child package edges
- excludes type-only imports (`TYPE_CHECKING`, `import type`)
- marks `__init__` aggregation and registration edges
- deduplicates logical edges after collapse

`units` / `edges` on `ArchitectureAnalysisView` are the **primary architectural graph**.
Raw package/edge counts remain on the view for coverage and evidence.

## Registration

`register_architecture_pack(registry)` — discoverable via `aimf rules list --category architecture`.

Assess merge requires both `[rules] enabled` and `[rules.architecture] enabled`.
