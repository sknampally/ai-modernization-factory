# Evidence and Confidence

## Evidence origins

| Origin | Meaning |
| ------ | ------- |
| `observed` | Extracted from source, config, lockfiles, or repository structure |
| `derived` | Deterministically calculated from observed evidence |
| `declared` | From configuration/metadata; not independently verified |
| `enterprise-declared` | From Enterprise Knowledge Graph YAML |
| `imported` | From an approved external artifact (e.g., advisory DB snapshot) |
| `runtime-imported` | From telemetry/profiling (future) |
| `externally-verified` | Confirmed by a trusted third-party integration (future) |

Repository findings today are primarily **observed** or **derived**. Enterprise
links are **enterprise-declared** until verified otherwise.

## Evidence strength

Strength is about how directly evidence supports a conclusion—not severity.

| Strength | Meaning |
| -------- | ------- |
| `direct` | Primary observation that alone supports the finding |
| `strong` | Multiple consistent direct signals |
| `supporting` | Corroborates but is not sufficient alone |
| `contextual` | Background that frames interpretation |
| `weak` | Suggestive only; high uncertainty |

## Evidence handling requirements

- **Provenance:** Every evidence item cites a safe location or subject reference.
- **Completeness:** Note when expected sources were missing.
- **Contradiction:** Prefer explicit conflict notes over silent overwrite.
- **Stale evidence:** Imported catalogs must carry version/as-of metadata when used.
- **Invalid evidence:** Reject credential-bearing URLs and secret-like payloads
  (align with existing security practices).
- **Deduplication:** Deterministic fingerprinting (as in Shared Rule Platform).
- **Excerpts:** Bounded; prefer fingerprints over large source dumps.
- **Citations:** Report appendix and CTO appendices link evidence → finding → rule.

## Confidence

**Confidence** = certainty in the assessment conclusion. It is **not** severity.

Recommended levels (align with Shared Rule Platform vocabulary where practical):

| Level | Meaning |
| ----- | ------- |
| `low` | Thin, incomplete, or highly heuristic evidence |
| `moderate` | Plausible with material uncertainty |
| `high` | Consistent, direct evidence; limited ambiguity |
| `very_high` / `certain` | Explicit facts (e.g., declared unsupported version) |

### Inputs to confidence

- evidence strength and quantity
- consistency across sources
- analysis coverage
- parser / language support maturity
- graph completeness
- enterprise context quality (when used)
- rule determinism
- unsupported or missing inputs

### Examples

| Case | Severity | Confidence |
| ---- | -------- | ---------- |
| Potential SQL injection from incomplete string-flow | high | low |
| Explicit unsupported framework version in lockfile | medium/high | very_high |
| Module exceeds size guideline | low | high |

Do not invent opaque mathematical confidence formulas. If a formula is introduced
later, it must be documented, deterministic, and testable.

## Relationship to existing models

Phase 3 `Finding` models emphasize evidence tuples and severity. Confidence may
appear in Shared Rule matches and metadata today. Future production wiring must
remain backward compatible and must not alter existing finding IDs.
