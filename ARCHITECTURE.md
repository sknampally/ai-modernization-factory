# AI Modernization Factory (AIMF) Architecture

**Version:** 0.1.0

## Purpose

AIMF analyzes application repositories and produces evidence-based modernization
assessments. Deterministic analysis discovers technologies, graphs, findings, and
recommendations. Optional AI enrichment adds a narrative over that evidence—never
inventing facts.

## Engineering philosophy

> **Deterministic analysis first. AI reasoning second.**

Benefits: repeatable analysis, explainable findings, lower hallucination risk,
budgeted token use, clear separation between facts and interpretation, and useful
output when AI is unavailable or fails.

## End-to-end assess pipeline

```text
                    aimf.toml / CLI
                           │
                           ▼
              Local path or GitHub clone
                           │
                           ▼
         Phase 1 AnalysisService (detect + analyzers + optional PMD)
                           │
                           ▼
              Repository Inventory → Repository Graph
                           │
                           ▼
         Knowledge Pipeline ← Engineering Knowledge Graph
                           │
                           ▼
                   Assessment Graph
                           │
                           ▼
              Rule Engine → findings.json
                           │
                           ▼
         Recommendation Engine → recommendations.json
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     HTML Report v2 + report.json   optional AI enrichment
                                        │
                                        ▼
                                 ai-enrichment.json
```

Topic docs: [docs/runtime.md](docs/runtime.md) and siblings under [docs/](docs/).

## Design principles

### Separation of responsibilities

| Layer | Responsibility |
| ----- | -------------- |
| Scanners | Acquire source (local / GitHub) |
| Detectors / analyzers | Phase 1 facts and analyzer findings |
| StaticAnalysisService | External providers (PMD today) |
| Inventory / graphs | Repository Graph, EKG, Assessment Graph |
| Rule Engine | Deterministic Phase 3 findings |
| Recommendation Engine | Deterministic Phase 3 recommendations |
| AI enrichment | Exactly one Bedrock call; narrative only |
| Knowledge store | Durable repository identity, snapshots, runs, immutable artifacts (SQLite) |
| Reporting | HTML Report v2 + JSON artifacts |
| Application | `AssessmentApplicationService` orchestration; knowledge ports/session; Agent Framework |
| CLI | Config, thin adapters, artifact retention |
| MCP | FastMCP tools/resources/prompts over application services |

### Evidence and immutability

* Findings and recommendations carry structured evidence and stable IDs.
* Graphs are immutable projections; rules never mutate them.
* AI may reference finding/recommendation IDs; it must not rewrite those artifacts.

## Modes

| Mode | AI calls | Artifacts |
| ---- | -------- | --------- |
| Deterministic (`--no-ai`) | 0 | Graphs, findings, recommendations, HTML/JSON |
| AI (`--with-ai`) | exactly 1 | Same + `ai-enrichment.json` on success |

AI enrichment failure warns and keeps deterministic output (CLI exit 0).

## Phase 1 analysis (shared)

```text
Repository
    → Technology detection
    → CompositeAnalyzer (ordered analyzers)
    → optional StaticAnalysisService (PMD)
    → Phase 1 RecommendationEngine
    → AnalysisResult
```

`aimf scan` reports `AnalysisResult` as text/JSON/HTML under `reports/`.
`aimf assess` continues into graphs → Phase 3 rules → recommendations → optional
AI → HTML Report v2.

### Analyzer order

1. RepositoryMetricsAnalyzer  
2. BuildDiscoveryAnalyzer  
3. BuildMetadataAnalyzer  
4. DependencyDiscoveryAnalyzer  
5. DependencyMetadataAnalyzer  
6. DependencyHealthAnalyzer  
7. CicdDiscoveryAnalyzer  
8. SecurityAnalyzer  
9. ArchitectureAnalyzer  
10. CloudReadinessAnalyzer  

### Static analysis (PMD)

```text
PMD XML → parser → observations → mapping/visibility → groups → Finding cards
```

Profiles: `focused` · `standard` · `comprehensive`. Critical/high findings are
never suppressed from HTML.

Future providers implement `StaticAnalysisProvider` and normalize into AIMF
observations/findings without changing orchestration ownership.

## Graphs

| Graph | Role |
| ----- | ---- |
| Repository Graph | Observations about one repository |
| Engineering Knowledge Graph | Reusable concepts (no repo identity) |
| Assessment Graph | Per-run projection/reference join |

See [docs/repository-graph.md](docs/repository-graph.md) and
[docs/assessment-graph.md](docs/assessment-graph.md).

## Rules and recommendations

```text
Assessment Graph → Rule Engine → findings.json
                              → Recommendation Engine → recommendations.json
```

No AI in either engine. Details: [docs/rule-engine.md](docs/rule-engine.md),
[docs/recommendation-engine.md](docs/recommendation-engine.md).

## AI enrichment

One Bedrock Converse call over a compact, budgeted context. Output validates
referenced finding and recommendation IDs. See [docs/ai-enrichment.md](docs/ai-enrichment.md).

Legacy `ModernizationAssessmentAgent` / `AIRecommendationResult` remain for
compatibility and bridging into report contracts; the assess path uses
`AiEnrichmentService` for the one-call enrichment artifact.

## HTML Report v2

Presentation-only view-model + renderer. Sections separate deterministic findings
and recommendations from optional AI enrichment. See
[docs/report-generation.md](docs/report-generation.md).

## Knowledge store (Phase 2B)

`AssessmentApplicationService` persists completed assessments side-by-side with
existing report artifacts:

```text
CLI → AssessmentApplicationService
        → full assessment pipeline (unchanged)
        → KnowledgeStore (snapshots, runs, content-addressed blobs)
        → existing report generation
```

Schema version 2 indexes repositories, snapshots, assessment runs, and artifact
metadata. Payloads live under `.aimf/knowledge/blobs/` (SHA-256, atomic write).
Reports are never read back into the store. Persistence finalization failure
fails the assessment; incomplete runs are never “latest completed.” Default
assessment remains full recomputation; incremental execution is opt-in only
(see Phase 2F below).

### Query services (Increment 3)

`KnowledgeQueryService` (`aimf.application.knowledge.queries`) is the
transport-neutral read API for durable knowledge. Future FastMCP, REST, CLI, and
agent adapters must call this service — not SQLite, blob paths, or report files.
Authoritative findings/recommendations are Phase 3 stable IDs. Snapshot
comparison uses persisted manifests. Graph component queries load immutable
graph JSON in memory with bounded depth (max 3).

### MCP adapter (Phase 2C)

`aimf mcp serve` starts a stdio FastMCP server named **CodeStrata**. Tools and
resources are thin adapters over `KnowledgeQueryService` and
`AssessmentApplicationService`. See [docs/mcp-server.md](docs/mcp-server.md).

### Agent Framework (Phase 2D / 2E)

`aimf.application.agents` provides deterministic orchestration
(`AgentOrchestrator`, Knowledge / Assessment / Validation agents) over the same
application services. Phase 2E adds thin adapters:

- CLI: `aimf agent review|assess|validate|compare|modernization-review`
- MCP: five `*_with_agents` tools

MCP and agents are sibling interfaces — agents must not call MCP internally.
Existing `aimf assess` and the 20 granular MCP tools remain unchanged.

See [docs/agent-framework.md](docs/agent-framework.md).

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

### Incremental planning (Phase 2F.1)

`aimf.application.incremental` classifies candidate vs previous manifests, analyzes
bounded impact, applies a conservative reuse policy, and emits a deterministic
`IncrementalAssessmentPlan`.

### Incremental execution (Phase 2F.2)

`IncrementalAssessmentExecutor` optionally executes eligible plans via inventory
merge + stage rebuild through the existing assessment pipeline, or falls back to
a normal full assessment. **`aimf assess` remains a full rebuild by default**;
execution requires explicit opt-in.

### Incremental operations (Phase 2F.3)

Post-execution validation, semantic equivalence, metrics, explainability, and
persisted `IncrementalExecutionRecord` provenance. Controlled rollout via
`[incremental].rollout_mode` (default `off`; production target `opt_in`).

Thin adapters:

- CLI: `aimf incremental plan|assess|explain`
- MCP: four additive incremental tools

```text
IncrementalAssessmentPlan
        → IncrementalAssessmentExecutor
        → Complete normal assessment result
        → Validation + metrics + explanations
        → IncrementalExecutionRecord → CLI / MCP
```

Details: [docs/incremental-assessment.md](docs/incremental-assessment.md),
[docs/knowledge-store.md](docs/knowledge-store.md).

### Enterprise Knowledge Graph (Phase 3)

YAML-declared enterprise architecture (organizations, applications, ownership,
standards) linked to CodeStrata repositories and assessments. Optional;
disabled by default. No graph database.

```text
Enterprise YAML → validate → EnterpriseKnowledgeGraph → CLI / MCP queries
```

Details: [docs/enterprise-knowledge-graph/README.md](docs/enterprise-knowledge-graph/README.md),
[ROADMAP.md](ROADMAP.md).

### Shared Rule Platform (Phase 4.1)

Transport-neutral rule infrastructure for future Analysis Intelligence packs.
Distinct from the Assessment Graph `RuleEngine` used by `aimf assess`.
Disabled by default; not wired into the default assessment pipeline.

```text
RuleExecutionContext → Registry → Planner → Executor → Finding mapper
```

Details: [docs/analysis-intelligence/shared-rule-platform.md](docs/analysis-intelligence/shared-rule-platform.md).

### Rule Platform Integration Bridge (Phase 4.1.1)

`LegacyRuleAdapter` and `RuleExecutionFacade` connect the Assessment Graph
`RuleEngine` to the Shared Rule Platform without changing `aimf assess`.
Adapted legacy evaluation preserves Finding IDs. See
[docs/analysis-intelligence/rule-platform-migration.md](docs/analysis-intelligence/rule-platform-migration.md).

### Assessment Framework (Phase 4.1.2)

Methodology for dimensions, rule taxonomy, evidence/confidence, scoring design,
business impact vs severity, modernization waves, and CTO report structure.
Documentation only—no production scoring. See
[docs/assessment-framework/README.md](docs/assessment-framework/README.md).

### Architecture Intelligence (Phase 4.2.1 / 4.2.1a / 4.2.2)

Initial production pack `architecture.core` (v1.0.0) registers seven SharedRules.
Phase **4.2.1a** hardens precision: architectural-unit selection (nested packages
collapsed), dependency normalization (parent/child, type-only, init/registration),
separated extraction vs classification coverage, and tighter coupling/direction
applicability. Discoverable via `aimf rules` / MCP. Merged into `aimf assess`
only when `[rules] enabled` and `[rules.architecture] enabled`.

Phase **4.2.2** adds Language Evidence Providers that collect and normalize
language facts for reuse by shared architecture rules. The provider pipeline is
**disabled by default** (`[evidence.language] enabled = false`); when disabled,
assessment behavior is unchanged.

```text
paths + source texts → ArchitectureAnalysisView
        → RuleExecutionFacade.execute_shared
        → RuleFindingMapper → Finding (merged with legacy RuleEngine)

opt-in:
providers → AggregatedLanguageEvidence → ArchitectureAnalysisView
```

Details: [docs/analysis-intelligence/architecture/README.md](docs/analysis-intelligence/architecture/README.md)
and [docs/analysis-intelligence/evidence-providers/README.md](docs/analysis-intelligence/evidence-providers/README.md).

Phase **4.2.3** adds Architecture Conclusions: deterministic grouping and
interpretation of architecture findings into explainable conclusions and
consolidated recommendations. Disabled by default
(`[analysis.architecture_conclusions] enabled = false`). Findings remain
unchanged. See
[docs/analysis-intelligence/architecture-conclusions/README.md](docs/analysis-intelligence/architecture-conclusions/README.md).

Phase **4.2.4** adds an optional Architecture Assessment section (`architecture-assessment.json`) composed from existing findings and optional conclusions. Disabled by default (`[assessment.sections.architecture] enabled = false`). See [docs/analysis-intelligence/architecture-assessment/README.md](docs/analysis-intelligence/architecture-assessment/README.md).

Phase **4.2.5** integrates that section into customer `report.json` and HTML via `ArchitectureReportAdapter` (`assessment.architecture`). Disabled by default (`[report.sections.architecture] enabled = false`). Schema remains `1.2` with an optional additive field. No scoring or AI narrative. See [docs/analysis-intelligence/architecture-reporting/README.md](docs/analysis-intelligence/architecture-reporting/README.md).

## Repository authentication

Private GitHub access uses credential **references** in config (`token_env`),
never secret values in TOML. Runtime credentials stay out of domain models and
reports. Authentication applies only to remote clones.

## Package layout (simplified)

```text
src/aimf/
├── cli/                 # Typer: version, scan, assess, agent, incremental, mcp
├── config/
├── application/         # assessment, knowledge queries, agents, incremental planning
├── infrastructure/      # SQLite knowledge store, blobs, Git revision observer
├── interfaces/          # FastMCP (and future REST) adapters
├── models/              # Phase 1 domain DTOs
├── domain/              # graphs, findings, recommendations, AI enrichment
├── services/            # analysis, inventory, knowledge, assessment
├── static_analysis/     # PMD provider boundary
├── ai/                  # enrichment + legacy agent / providers
├── reporters/           # aimf scan reporters
├── reporting/           # assess HTML/JSON (incl. html_v2/)
└── repository_auth/
```

## Configuration

Primary file: `aimf.toml` (repository, AWS, AI, static analysis, reporting).
Secrets belong in environment / `.env` (gitignored), never in committed config.

## Retention

Completed assess/scan runs keep the latest **three** per repository name; older
run directories are pruned after successful writes. Report retention does **not**
delete knowledge-store rows or blobs (knowledge retention is deferred).

## Out of scope for v0.1.0

* Multi-step agent / MCP tool loops for enrichment
* Lockfile-complete dependency resolution
* Assisted code refactoring
* Hosted SaaS control plane

## Related documents

* [README.md](README.md) — product overview and quick start  
* [docs/](docs/) — canonical topic documentation  
* [CHANGELOG.md](CHANGELOG.md) — release notes  
* [examples/README.md](examples/README.md) — commands and expected outputs  
