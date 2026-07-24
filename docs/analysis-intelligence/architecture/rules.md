# Architecture Rules

All rules: version `1.0.0`, pack `architecture.core`, Community-applicable unless noted.
Precision hardened in **4.2.1a**.

## `architecture.dependency-cycle`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.dependency-structure` |
| Operates on | primary architectural units (post-collapse) |
| Severity | medium (2-node); high (larger) |
| Skips | cycles involving composition-root or registration units; parent/child package 2-cycles; subsumed longer cycles |

Evidence includes normalized cycle path, edge kinds, and raw package provenance.

## `architecture.invalid-dependency-direction`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.layering` |
| Requires | classification coverage ≥ 0.25 with ≥2 medium-confidence layered units |
| Skips | composition roots; low-confidence classifications; init/registration edges |
| Evidence | governing direction rule (`forbid:source>target`) |

Ambiguous classification → not applicable (never speculative).

## `architecture.layer-boundary-violation`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.boundaries` |
| Same applicability | as invalid-dependency-direction |
| Detects | presentation/api → persistence/infrastructure skips |

## `architecture.excessive-cross-module-coupling`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.coupling` |
| Subjects | comparable architectural modules only (excludes composition-root, registration, test) |
| Thresholds | absolute `outgoing_module_threshold` **and** peer-relative `median * relative_multiplier` |
| Evidence | fan-out, unique primary targets, raw packages, peer population |

## `architecture.component-concentration`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.modularity` |
| Subjects | comparable architectural modules |
| Metric | incident edge share on included primary edges |

## `architecture.framework-leakage`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.boundaries` |
| Requires | reliably classified domain units |
| Patterns | initial Java JPA / Spring Web set |

## `architecture.enterprise-standard-mismatch`

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.enterprise-standards` |
| Edition | Enterprise only |

## Overlap

| Pair | Relationship |
| ---- | ------------ |
| cycle + invalid direction | May share subjects; different conclusions (cycle vs layer rule) — both retained |
| coupling + concentration | Related connectivity views; both retained when thresholds met |
| direction + boundary | Boundary is a specialized skip; direction is general forbid |

Findings carry executive/recommendation metadata for later report grouping; no silent discard of distinct evidence.
