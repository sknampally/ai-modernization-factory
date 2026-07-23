# Rule authoring (Phase 4.1+)

Implement `SharedRule`:

1. Immutable `RuleMetadata` with stable `rule_id` and `RuleVersion`
2. `evaluate_applicability(context) -> RuleApplicability`
3. `evaluate(context) -> SharedRuleEvaluationResult`

Rules must not:

- load files / call subprocess / network / AI
- query SQLite or YAML
- mutate graphs
- emit CLI/MCP output

Register explicitly via `RuleRegistry.register` / `register_collection`.
No dynamic imports or entry-point plugins in Phase 4.1.

Prefer `RuleTestHarness` for unit tests. See [testing-rules.md](testing-rules.md).
