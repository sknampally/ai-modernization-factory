# Validation

`EnterpriseManifestValidationService` runs deterministic stages:

1. Parse / envelope
2. Schema (`apiVersion`, `kind`)
3. Identity and duplicates
4. Referential integrity
5. Relationship kind constraints
6. Hierarchy cycle detection
7. Repository resolution
8. Security (secrets / credential URLs)
9. Graph-build readiness

`EnterpriseGraphValidationService` (final) checks unique IDs, endpoints, bounds,
fingerprints, and provenance before save.

Issues include stable codes, severity, safe relative locations, and blocking
flags. Absolute paths and stack traces are not exposed.

Exit codes for `aimf enterprise validate`: `0` valid, `1` validation errors,
`2` load/config failure.
