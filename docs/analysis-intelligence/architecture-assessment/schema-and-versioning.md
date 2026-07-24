# Schema and versioning

- Section schema version: `1.0.0` (independent of rule pack version)
- Pack version recorded separately (`architecture.core` / `1.0.0`)
- When integration is disabled: section is **absent** (existing assessment shape)
- When integration is enabled: section is **present**, including `disabled` status
