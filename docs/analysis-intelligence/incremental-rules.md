# Incremental rules

Each `RuleMetadata` declares `incremental_behaviors`.
`rule_invalidation_fingerprint` combines rule ID, version, config, and context.

Phase 4.1 is **conservative**: plans always recompute (`reuse_claimed=false`,
`actual_reuse_count=0`). Selective reuse requires proven compatibility,
provenance, equivalence, and telemetry — deferred.
