# Incremental assessment (Phase 2F)

**Status:** Phase 2F complete (2F.1 planning + 2F.2 execution + 2F.3 operations).

Public product name: **CodeStrata**. Internal package/CLI/config remain `aimf`.

## Phase 2F roadmap

| Sub-phase | Scope |
| --------- | ----- |
| **2F.1** | Fingerprints, change classification, impact, reuse policy, deterministic plan |
| **2F.2** | Selective execution, inventory merge, stage rebuild, merge validation, full-rebuild fallback |
| **2F.3 (this)** | Post-execution validation, semantic equivalence, telemetry, explainability, provenance, controlled CLI/MCP rollout |

## Purpose

Make incremental assessment **operationally trustworthy and inspectable** while
keeping full assessment as the default.

```text
Incremental plan
      │
      ▼
Incremental executor
      │
      ▼
Complete assessment result
      │
      ▼
Validation + equivalence + metrics + explanations
      │
      ▼
Incremental execution record
      │
      ├─ CLI (`aimf incremental`)
      └─ MCP (additive tools)
```

## Core correctness rule

For every supported incremental scenario, the deterministic incremental result
must be **semantically equivalent** to a clean full assessment of the same
repository state.

- Validation is deterministic (no LLM)
- Equivalence and explainability use no AI
- Fallback is expected safe behavior
- No partial result is trusted or persisted as a complete incremental result
- `aimf assess` remains a full rebuild
- AI artifact reuse remains disabled

## Rollout modes

```toml
[incremental]
rollout_mode = "off"   # default
```

| Mode | Planning | Incremental execution |
| ---- | -------- | --------------------- |
| `off` | blocked | blocked |
| `plan_only` | allowed | blocked |
| `opt_in` | allowed | explicit CLI/MCP/API only |
| `default_with_fallback` | modeled/tested | **not** activated as default in 2F.3 |

Legacy `enabled` / `execution_enabled` map safely when `rollout_mode` is omitted.
Conflicting combinations are rejected. Hard safety fallbacks cannot be disabled.

## Configuration

```toml
[incremental]
rollout_mode = "off"
enabled = false
execution_enabled = false
validate_after_execution = true
persist_execution_records = true
enable_equivalence_check = false
max_explanations = 500
max_equivalence_differences = 100
allow_ai_reuse = false
fallback_on_validation_failure = true
fallback_on_metric_inconsistency = true
```

## CLI (explicit opt-in)

```bash
aimf incremental plan <repository> [--previous-run-id ...] [--json]
aimf incremental assess <repository> [--previous-run-id ...] [--with-ai] [--equivalence-check] [--json]
aimf incremental explain <execution-id> [--kind ...] [--subject-id ...] [--limit N] [--json]
```

- Exit `0`: trusted completion (including successful full fallback)
- Exit `1`: blocked / untrusted validation
- Exit `2`: configuration or execution failure

`aimf assess` is unchanged.

## MCP (additive)

Four new tools (existing 20 granular + 5 agent tools unchanged):

1. `create_incremental_assessment_plan`
2. `execute_incremental_assessment`
3. `get_incremental_execution`
4. `explain_incremental_execution`

## Validation, metrics, explainability

- `IncrementalValidationService` — execution, plan, fallback, reuse, AI integrity; optional semantic equivalence
- `AssessmentSemanticComparator` — canonical normalization; ignores run/snapshot/timestamps only
- `IncrementalMetricsCalculator` — actual reuse/recompute ratios; fallback counts as zero reuse
- `IncrementalExplainabilityService` — deterministic reason codes; no speculative language
- `IncrementalExecutionRecord` — primary DTO for CLI/MCP inspection
- Provenance under `{knowledge}/incremental_executions/` (additive JSON records)

## Supported scenarios

- Explicit opt-in via `aimf incremental assess`, MCP execute tool, or
  `assess_incrementally_if_safe(...)` with rollout `opt_in`
- Eligible no-change / metadata-only / incremental-candidate plans
- Successful full-rebuild fallback (structured success)
- Post-execution validation + metrics + explanations + provenance

## Unsupported / fallback scenarios

- `aimf assess` (always full)
- `rollout_mode = off` (default)
- `plan_only` for execution
- engine / schema / fingerprint incompatibility
- truncated / unknown impact
- AI reuse (always disabled)
- any case where safety cannot be proven → full rebuild

## Golden equivalence testing

Use `tests/application/incremental/equivalence_helpers.py` to compare
incremental vs clean full `AssessmentCommandResult` artifacts without reading
report files.

## Security

No caller-defined steps, fingerprints, SQL, blob access, report reads, shell/Git
commands, path traversal, unbounded explanations, or disabling hard fallbacks.
Execution records never expose absolute paths, credentials, or source code.

## Phase 2 completion

Phase 2 (knowledge + agents + MCP + incremental foundation through 2F.3) is
complete for controlled opt-in use. Full assessment remains the default product
path.

## Next phase (deferred)

Phase 3 delivers the Enterprise Knowledge Graph (optional YAML). Analysis
Intelligence is Phase 4; GitHub PR review remains Phase 6.
