# Report JSON

Optional key under `assessment.architecture`.

Decision: keep `schema_version` at **1.2**. The architecture section is an
additive optional field. Old report.json artifacts remain readable. When
architecture reporting is disabled or the section is unavailable, the key is
omitted.

Semantics:

- omitted → section not included
- present → presentation payload with explicit `status`
- empty collections → `[]` / `()` equivalents in JSON
- unsupported coverage → display string, not `0`
