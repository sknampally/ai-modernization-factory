# Rule lifecycle

1. Author + unit test with harness
2. Explicit registry registration in application composition
3. Plan (`RulePlanner`) — deterministic selection
4. Execute (`RuleExecutor`) — isolated failures
5. Suppress (application service) — matches remain inspectable
6. Map to `Finding` via existing `Finding.create` / `build_finding_id`
7. Telemetry + explainability

Production packs begin in Phase 4.2. Phase 4.1 ships infrastructure only.
