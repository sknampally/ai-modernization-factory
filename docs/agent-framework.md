# CodeStrata Agent Framework

Phase 2D adds a transport-neutral **Agent Framework** that coordinates existing
application services. Agents are application-level orchestrators — not MCP
clients, CLI adapters, chat bots, or alternate business-logic implementations.

Public product name: **CodeStrata**. Internal package/CLI/config remain `aimf`.

## Purpose

Provide bounded, deterministic workflows that:

- review persisted repository knowledge
- run a new assessment through `AssessmentApplicationService`
- validate persisted assessment completeness
- compare repository snapshots
- assemble grounded repository and modernization review packages

Agents **orchestrate**; they do not reimplement scanning, graph construction,
rules, recommendations, persistence, Bedrock, or report generation.

## Deterministic-first design

Core workflow behavior works fully without AI:

- agent selection and step order are fixed plans
- validation, evidence retrieval, and snapshot comparison are deterministic
- AI is never required to decide whether an assessment completed

This increment does **not** implement LLM-based tool selection, ReAct loops,
autonomous retries, or reflection.

## Architecture

```text
CLI / MCP / REST
        │
        ├───────────────┐
        │               │
        ▼               ▼
Agent Framework    Application Services
        │               ▲
        └───────────────┘
```

- MCP and agents are **sibling** interfaces over the same application services.
- Agents call `KnowledgeQueryService` and `AssessmentApplicationService` directly.
- Agents must **not** call the FastMCP server, open SQLite, read blobs, or read
  `report.json` / `report.html`.

Package: `aimf.application.agents`

| Module | Role |
| ------ | ---- |
| `orchestrator.py` | Explicit workflow coordination |
| `knowledge_agent.py` | Persisted knowledge assembly |
| `assessment_agent.py` | Assessment execution |
| `validation_agent.py` | Completeness / grounding checks |
| `planner.py` | `DeterministicAgentPlanner` + future `AgentPlanner` protocol |
| `policies.py` | Conservative execution bounds |
| `evidence.py` | Grounded evidence records |
| `factory.py` | Injectable composition |

## Workflows

| Workflow | Entry |
| -------- | ----- |
| Repository review | `AgentOrchestrator.review_repository` |
| Repository assessment | `AgentOrchestrator.assess_repository` |
| Snapshot comparison | `AgentOrchestrator.compare_repository_snapshots` |
| Assessment validation | `AgentOrchestrator.validate_assessment` |
| Modernization review | `AgentOrchestrator.modernization_review` |

Each workflow has a typed request/result, explicit steps, bounded execution,
captured evidence, and a validation outcome when applicable.

### Assessment workflow (recommended order)

1. KnowledgeAgent resolves prior repository context (when registered)
2. KnowledgeAgent captures previous assessment IDs
3. AssessmentAgent calls `AssessmentApplicationService`
4. KnowledgeAgent retrieves the new persisted run
5. ValidationAgent validates the persisted run
6. Orchestrator returns the grounded result

### Review workflow

1. Resolve repository + latest completed assessment
2. Retrieve findings, recommendations, components, optional AI artifacts
3. Validate evidence completeness
4. Assemble `RepositoryReviewResult`

## Evidence model

Conclusions are grounded with `AgentEvidence`:

- stable `source_id` / `evidence_id`
- `source_kind` (repository, run, finding, recommendation, …)
- concise summary
- `deterministic` flag
- related IDs

AI content may **reference** evidence; it cannot replace evidence. Full source
code, blob paths, credentials, and knowledge-store paths are never stored in
evidence.

## Validation model

`ValidationAgent` checks runs, artifacts, findings, recommendations, graph
references, and optional AI artifacts through query DTOs only.

Issues use severities: `info`, `warning`, `error`, `blocking`.

When `stop_on_blocking_validation` is true (default), the orchestrator marks the
workflow `blocked` instead of successful completion.

Phase 1 UUID findings are never treated as authoritative.

## Policies

```toml
[agents]
enabled = true
max_steps = 10
max_findings = 100
max_recommendations = 100
max_components = 100
dependency_depth = 2
stop_on_blocking_validation = true
```

Omitted `[agents]` keeps defaults. Dependency depth cannot exceed 3. Existing
`aimf.toml` files remain valid without this section. AI provider settings stay
under `[ai]` / `[aws]`.

## Composition

```python
from aimf.application.agents import create_agent_orchestrator

orchestrator = create_agent_orchestrator(
    query_service=queries,
    assessment_service=assessment_service,  # optional for review-only
    policy=None,  # or AgentExecutionPolicy(...)
)
result = orchestrator.review_repository(
    RepositoryReviewRequest(repository_identifier=repo_id)
)
```

Tests should inject fake services. Importing `aimf.application.agents` does not
open a database or call Bedrock.

## Optional CLI / MCP integration

**Deferred in this increment** to keep the framework independently usable and
avoid broadening the surface area:

- `aimf agent review|assess|validate` CLI commands
- high-level MCP tools (`review_repository_with_agents`, …)

Existing `aimf assess` and the 20 MCP tools remain unchanged. When added later,
those adapters must call `AgentOrchestrator` only — no duplicated workflow logic.

## Security

- No credentials, AWS profiles, SQL, blob paths, or stack traces in agent results
- Unexpected exceptions are wrapped as agent errors
- Structured logs include workflow/run/repository IDs and statuses only

## Current limitations

- No LLM planner (extension point only: `AgentPlanner`)
- No autonomous loops or retries
- No new recommendation / rule / graph engines
- Optional CLI and MCP agent tools deferred
- Review narratives remain deterministic aggregations (no required AI prose)

## Next Phase 2 capability

Likely: thin CLI/MCP adapters over the Agent Framework, then incremental scanning
or PR-oriented review — without changing agent→application-service boundaries.
