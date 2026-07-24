# CodeStrata Platform Architecture

**Document type:** Implementation-based inventory (not a design proposal)  
**Source of truth:** Current repository code, tests, and configuration  
**Product name:** CodeStrata  
**Implementation package / CLI:** `aimf` (not renamed)  
**Package version:** `0.1.0` (`pyproject.toml`)

When documentation elsewhere conflicts with this inventory, **implementation wins**.
Claims that could not be verified are marked **Not confirmed in the current implementation.**

---

## 1. Purpose

CodeStrata is an engineering assessment platform that analyzes application
repositories, produces deterministic findings and recommendations, optionally
enriches them with architecture intelligence and AI summaries, persists knowledge,
and exposes results through CLI, HTML/JSON reports, and MCP.

### Separated purposes (as implemented)

| Layer | What exists today |
| ----- | ----------------- |
| Repository analysis platform | Scan local/GitHub repos; inventory; technology detection; Phase 1 analyzers; optional PMD |
| Intelligence framework | Shared Rule Platform + Language Evidence Providers + Architecture pack/conclusions |
| Assessment framework | `AssessmentApplicationService` orchestration; findings/recommendations artifacts; optional architecture assessment section |
| Report generation | HTML v2 + `report.json` (schema 1.2); does **not** yet render architecture assessment sections |
| MCP exposure | FastMCP “CodeStrata” server over stdio with tools/resources/prompts |
| Agent capabilities | Application `AgentOrchestrator` (deterministic multi-agent workflows) + separate AI enrichment agent path |
| Future product capabilities | Technical Debt / Security / Performance / Modernization intelligence packs; full CTO report redesign — **planned** |

---

## 2. Architectural Principles Observed in the Implementation

| Principle | Evidence |
| --------- | -------- |
| Domain-driven separation | Packages under `src/aimf/domain/` (graph, findings, rules, evidence, architecture, enterprise, …) vs `application/` vs `services/` vs `interfaces/` |
| Deterministic analysis | Stable finding IDs (`domain/findings/ids.py`); stable JSON via `dumps_stable_json` (`services/artifact_serialization.py`); sorted registries |
| Evidence-first assessment | Architecture rules consume `ArchitectureAnalysisView`; language providers produce provenance-bearing evidence |
| Findings as source observations | Canonical `Finding` models; conclusions cite `source_finding_ids` without replacing findings |
| Conclusions as enrichment | `ArchitectureConclusionService`; `[analysis.architecture_conclusions] enabled = false` by default |
| Language-neutral rules | SharedRules evaluate normalized views; providers supply language facts (`application/evidence/language/`) |
| Provider-based evidence collection | `LanguageEvidenceProviderRegistry` + planner/executor/aggregator |
| Optional enterprise context | `[enterprise] enabled = false`; enterprise-standard rule/conclusion require context |
| Disabled-by-default capability rollout | Rules, architecture pack, evidence, conclusions, architecture assessment section, incremental, static analysis |
| Stable identifiers | Finding, conclusion, cluster, recommendation-group, section, limitation, trace edge IDs |
| Traceability | `ArchitectureTraceabilityIndex` edges in architecture assessment section |
| Failure isolation | Rule/conclusion/provider failures recorded; assessment continues where designed; policy try/except in conclusion service |
| Backward compatibility | Optional fields on `AssessmentCommandResult`; architecture section absent when disabled; HTML schema unchanged |

---

## 3. Top-Level Architecture

```text
                    ┌─────────────────────────────────────────┐
                    │  CLI (aimf)  /  MCP (CodeStrata/stdio)  │
                    │  optional: AgentOrchestrator workflows  │
                    └───────────────────┬─────────────────────┘
                                        │
                    ┌───────────────────▼─────────────────────┐
                    │     AssessmentApplicationService        │
                    │     (or AnalysisService for scan)       │
                    └───────────────────┬─────────────────────┘
                                        │
     Repository ──► Scanner ──► Inventory/Phase1 Analysis ──► AnalysisResult
                                        │
                    ┌───────────────────▼─────────────────────┐
                    │        GraphAssessmentPipeline          │
                    │  manifest → repo graph → EKG → bind →   │
                    │            assessment graph             │
                    └───────────────────┬─────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
     Legacy RuleEngine        [opt] Language Evidence      [opt] architecture.core
     (Phase 3 rules)          providers → Aggregated       Shared Rule Platform
              │               Evidence → ArchView                 │
              └─────────────────────────┬─────────────────────────┘
                                        ▼
                                   Findings.json
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
           RecommendationEngine  [opt] Conclusions   [opt] Arch Assessment
                                   .json                Section .json
                    │
                    ▼
         [opt] AI enrichment ──► report.html + report.json
                    │
                    ▼
         Knowledge store (SQLite) snapshot blobs
```

Optional paths are gated by configuration (see §17). Future CTO report
consumption of architecture sections is **not** shown as implemented.

---

## 4. Runtime Pipelines

### Repository Analysis Pipeline

```text
Repository source (path | GitHub URL)
  → LocalRepositoryScanner | GitHubRepositoryScanner
  → RepositoryInventoryBuilder / Phase1RepositoryAdapter
  → Technology detectors + CompositeAnalyzer (Phase 1)
  → optional PmdProvider
  → AnalysisResult
```

Primary locations: `services/scanners/`, `services/inventory/`, `services/analysis_service.py`, `services/default_pipeline.py`.

### Shared Rule Pipeline

```text
RuleRegistry.register
  → RulePlanner.plan(context)
  → RuleExecutor.execute
  → SharedRuleEvaluationResult (matches/records)
  → RuleFindingMapper → Finding
  → (legacy RecommendationEngine for graph recommendations)
  → findings.json / suppression (platform support) / telemetry
```

Primary locations: `application/rules/{registry,planner,executor,facade,finding_mapper}.py`, `domain/rules/`.

Legacy path still used in assess: `services/rule_engine/RuleEngine` for Phase 3 graph rules; architecture pack merges via Shared Rule Platform.

### Language Evidence Pipeline

```text
LanguageEvidenceProviderRegistry
  → LanguageEvidenceProviderPlanner
  → LanguageEvidenceProviderExecutor
  → LanguageEvidenceAggregator
  → AggregatedLanguageEvidence (+ provenance/coverage/fingerprint)
  → optional architecture_view_from_aggregated_evidence
```

Primary: `application/evidence/language/`. Default **disabled** (`evidence.language.enabled = false`).

### Architecture Intelligence Pipeline

```text
ArchitectureAnalysisView (legacy builder or language evidence)
  → architecture.core SharedRules
  → Findings
  → [opt] relationships → clusters → conclusion policies
  → recommendation groups
  → [opt] ArchitectureAssessmentAssembler → architecture-assessment.json
```

### Assessment Pipeline

```text
AssessmentApplicationService.run
  → scan → AnalysisService → GraphAssessmentPipeline
  → RuleEngine + optional architecture pack
  → optional conclusions + architecture assessment section
  → RecommendationEngine
  → optional AI enrichment
  → HTML/JSON reports
  → knowledge session complete
```

Location: `application/assessment/service.py`.

### Reporting Pipeline

```text
ModernizationReportInput
  → build_assessment_json_document (schema 1.2)
  → HTML v2 builder/renderer
  → report.json + report.html
```

Architecture assessment/conclusion artifacts are **not** consumed by reporting today.

### MCP Pipeline

```text
stdio → FastMCP (CodeStrata)
  → tool/resource handler
  → KnowledgeQueryService / AssessmentApplicationService / …
  → bounded structured response (run_bounded)
```

### Agent Pipeline

**Application agents (implemented):**

```text
CLI/MCP → AgentOrchestrator
  → DeterministicAgentPlanner
  → KnowledgeAgent / AssessmentAgent / ValidationAgent
  → application services (may call AssessmentApplicationService)
```

**AI agents (partial / legacy relative to enrichment):**

```text
AI-enhanced assess → enrichment service (preferred)
  (ModernizationAssessmentAgent / AIMFToolRegistry still present)
```

Agents are **not** required for deterministic analysis.

---

## 5. Domain Model

| Area | Purpose | Key models | Ownership | IDs / serialization |
| ---- | ------- | ---------- | --------- | ------------------- |
| Repository | Manifest identity & files | `RepositoryManifest`, `RepositoryIdentity`, fingerprints | `domain/repository` | Deterministic fingerprints |
| Graph kernel | Shared node/edge primitives | `GraphNode`, `GraphRelationship`, `GraphSnapshot` | `domain/graph` | Schema versioned snapshots |
| Repository graph | Structural/dependency graph | `RepositoryGraph` | `domain/repository_graph` | JSON artifact |
| Engineering knowledge | Catalog knowledge | `EngineeringKnowledgeGraph` | `domain/engineering_knowledge` | Builtin catalog load |
| Knowledge binding | Bind repo facts to knowledge | `KnowledgeBindingResult` | `domain/knowledge_binding` | JSON |
| Assessment graph | Assessment-oriented graph | `AssessmentGraph` | `domain/assessment_graph` | JSON |
| Enterprise | Declared enterprise model | `EnterpriseKnowledgeGraph`, entities | `domain/enterprise` | File JSON, optional |
| Findings | Observed conditions | `Finding`, `RuleEvaluationResult` | `domain/findings` | Stable `finding:…` IDs |
| Recommendations | Actions | `Recommendation`, `RecommendationResult` | `domain/recommendations` | Versioned results |
| Rules | Shared rule platform | `SharedRule`, `RuleExecutionContext`, results | `domain/rules` | Rule ID + version |
| Architecture view | Normalized architecture facts | `ArchitectureAnalysisView` | `domain/rules/architecture` | Graph fingerprint |
| Language evidence | Provider facts | `LanguageEvidenceBundle`, `AggregatedLanguageEvidence` | `domain/evidence/language` | Provider fingerprints |
| Conclusions | Interpretations | `ArchitectureConclusion`, `ConsolidatedRecommendation` | `domain/architecture/conclusions` | Stable conclusion IDs |
| Architecture assessment | Assessment section | `ArchitectureAssessmentSection` | `domain/architecture/assessment` | `assessment.architecture` @ 1.0.0 |
| AI enrichment | Optional narrative enrichment | `AiEnrichmentResult` | `domain/ai_enrichment` | Artifact JSON |
| Report models | Customer report input | `ModernizationReportInput` | `reporting/modernization_models.py` | `extra=forbid` |
| MCP models | Transport DTOs | `interfaces/mcp/models.py` | interfaces | Bounded payloads |

Invariants commonly enforced via Pydantic `frozen=True`, `extra="forbid"`, and validation helpers in `domain/graph/validation.py`.

---

## 6. Repository Discovery and Inventory

| Topic | Implementation |
| ----- | -------------- |
| Supported sources | Local path; GitHub URL (`LocalRepositoryScanner`, `GitHubRepositoryScanner`) |
| Traversal / exclusions | Scanner excludes default dirs (e.g. `.git`); tests cover exclude behavior |
| Classification | `services/inventory/classification.py`, language helpers |
| Language detection | Inventory language module + evidence path detection |
| Build-file detection | Phase 1 `BuildDiscoveryAnalyzer`, `BuildMetadataAnalyzer` |
| Identity / fingerprints | `RepositoryIdentity`, `RepositoryFingerprint` |
| Incremental | Opt-in `[incremental]` planner/executor; not default assess path |
| Failure handling | Assessment raises `AssessmentCommandError` on scan/config failures |
| Extension points | Inject scanner / analysis service into `AssessmentApplicationService.run` |

---

## 7. Graph and Knowledge Layers

**No graph database is implemented.** Graphs are in-memory domain objects serialized to JSON (and optionally stored as knowledge-store blobs).

| Layer | Purpose | Persistence | Consumers | Maturity |
| ----- | ------- | ----------- | --------- | -------- |
| Repository Graph | Files/modules/deps | `graphs/repository-graph.json` | Rule engine, architecture view builders | Production-capable |
| Engineering Knowledge Graph | Builtin catalog | `graphs/engineering-knowledge-graph.json` | Bindings | Production-capable |
| Knowledge bindings | Match observations | `graphs/knowledge-bindings.json` | Assessment graph | Production-capable |
| Assessment Graph | Assessment nodes/edges | `graphs/assessment-graph.json` | Phase 3 rules/recommendations | Production-capable |
| Enterprise Knowledge Graph | Declared YAML enterprise model | File repo under knowledge dir | Enterprise CLI/MCP; optional architecture enterprise rule | Optional / production-capable with limitations |

Builders: `services/graph_assessment/` (`GraphAssessmentPipeline`, assemblers, extractors); enterprise: `application/enterprise/graph_builder.py`.

---

## 8. Shared Rule Platform

```text
SharedRule (+ metadata)
    → RuleRegistry
    → RulePlanner (applicability, order)
    → RuleExecutor (per-rule isolation)
    → matches/records
    → RuleFindingMapper → Finding
```

| Concern | Location |
| ------- | -------- |
| Contract | `domain/rules/contracts.py` |
| Registry | `application/rules/registry.py` |
| Planner / executor | `application/rules/planner.py`, `executor.py` |
| Facade | `application/rules/facade.py` (`evaluate`, `evaluate_adapted`, `execute_shared`) |
| Packs | `application/rules/architecture/pack.py` — only production pack: `architecture.core` **1.0.0** |
| Suppression | Domain/platform support (Shared Rule Platform); assess path preserves findings visibility policies |
| CLI | `aimf rules list|inspect|explain` |
| MCP | `list_shared_rules`, `get_shared_rule`, `explain_shared_rule_metadata`, `get_shared_rule_platform_summary` |
| Config | `[rules] enabled=false`, `[rules.architecture] enabled=false` |

Legacy Phase 3 `RuleEngine` remains the default assess rule path; architecture pack is merged when enabled.

---

## 9. Language Evidence Provider Platform

| Component | Location |
| --------- | -------- |
| Registry | `LanguageEvidenceProviderRegistry` |
| Planner / executor / aggregator | `planner.py`, `executor.py`, `aggregator.py` |
| Service | `LanguageEvidenceService` |
| Architecture adapter | `architecture_adapter.py` |
| Legacy adapter | `legacy_adapter.py` (`language.legacy.adapter`) |

### Confirmed providers

| Provider ID | Version | File |
| ----------- | ------- | ---- |
| `language.python.core` | 1.0.0 | `providers/python_provider.py` |
| `language.java.core` | 1.0.0 | `providers/java_provider.py` |
| `language.javascript.core` | 1.0.0 | `providers/javascript_provider.py` |

Capabilities include source units, dependencies, frameworks (provider-specific).  
CLI: `aimf evidence …`. MCP: `list_evidence_providers`, `inspect_evidence_provider`, `list_evidence_capabilities`, `explain_evidence_provider`.  
Default: **disabled**.

---

## 10. Intelligence Pack Architecture

**Pattern status:** Emerging / reference-implemented by Architecture Intelligence; **not** a generic pack SDK beyond SharedRule registration + optional conclusions/assessment assembly.

Reference flow (Architecture):

evidence/view → rules → findings → (relationships/clusters/conclusions) → (assessment section) → artifacts/CLI/MCP

### Intelligence domain inventory

| Domain | Status |
| ------ | ------ |
| Architecture | **Implemented** (`architecture.core` 1.0.0 + conclusions + assessment section) |
| Technical Debt | **Not found** as pack (enum category only; ROADMAP 4.3 not started) |
| Security | **Foundational support only** — Phase 1 `SecurityAnalyzer`; no SharedRule security pack |
| Performance | **Not found** as pack (category enum; ROADMAP 4.5 not started) |
| Cloud and Platform | **Foundational support only** — Phase 1 `CloudReadinessAnalyzer` |
| AI Readiness | **Not found** as intelligence pack |
| Modernization | **Partial** — recommendations/report phases exist; no Modernization Intelligence pack (ROADMAP 4.6) |

---

## 11. Architecture Intelligence

| Item | Implementation |
| ---- | -------------- |
| Pack | `architecture.core` **1.0.0** |
| Rules (7) | dependency-cycle, invalid-dependency-direction, layer-boundary-violation, excessive-cross-module-coupling, component-concentration, framework-leakage, enterprise-standard-mismatch |
| Deferred rule | `architecture.service-dependency-cycle` |
| Precision hardening | Unit selection, dependency normalization, extraction vs classification coverage (4.2.1a) |
| View | `ArchitectureAnalysisView` |
| Conclusions | 7 policies; positive-boundary disabled by default |
| Assessment section | `ArchitectureAssessmentSection` schema 1.0.0 |
| Artifacts | `architecture_conclusions.json`, `architecture-assessment.json` |
| Report integration | Optional `assessment.architecture` via adapter (4.2.5; disabled by default) |
| Defaults | Pack/conclusions/section all disabled unless configured |

Distinction:

- **Finding** — observed rule condition  
- **Conclusion** — deterministic interpretation of related findings  
- **Recommendation group** — coordinated actions  
- **Assessment section** — formal assessment composition  
- **Report presentation** — not yet architecture-aware

---

## 12. Assessment Framework

| Concern | Status |
| ------- | ------ |
| Orchestration | `AssessmentApplicationService` |
| Canonical findings/recommendations | `findings.json`, `recommendations.json` |
| Assessment sections | Architecture section only (optional) |
| Section statuses | `ArchitectureAssessmentStatus` enum |
| Coverage / confidence / limitations / traceability | Present on architecture section |
| Schema versioning | Architecture section `1.0.0`; customer JSON `1.2` |
| Generic multi-section framework | **Partial** — config under `assessment.sections.architecture` is architecture-specific; no generic section registry found |

Evidence of coupling: assembler and MCP tools are architecture-named; `list_assessment_sections` currently advertises the architecture section primarily.

---

## 13. Reporting Platform

| Component | Location / status |
| --------- | ----------------- |
| Models | `reporting/modernization_models.py` (`extra=forbid`) |
| JSON | `assessment_json.py` schema **1.2** |
| HTML v2 | `reporting/html_v2/` |
| Writers | `modernization_serialization.py` (atomic replace) |
| Charts / executive CTO layout | Full CTO redesign still planned; architecture section integrated in 4.2.5 |
| Architecture section consumption | **Not implemented** |

---

## 14. MCP Platform

| Concern | Detail |
| ------- | ------ |
| Entry | `aimf mcp serve` → `interfaces/mcp/server.py` / `factory.py` |
| Transport | **stdio only** (`McpSettings.transport`) |
| Name | `CodeStrata` |
| Bounds | `run_bounded` / mapping helpers; tools return structured dicts without raw source dumps |

### Tool / resource inventory (summary)

| Group | Examples | Status |
| ----- | -------- | ------ |
| Repository | `list_repositories`, `get_repository` | Implemented |
| Assessment history | `list_assessments`, `get_assessment`, `get_latest_assessment`, `run_assessment` | Implemented |
| Findings / recommendations / components / snapshots / artifacts | list/get/explain families | Implemented |
| Agents | `*_with_agents` tools | Implemented when orchestrator composed |
| Incremental | plan/execute/explain tools | Implemented (feature-gated) |
| Enterprise | validate/build/query/impact tools + resources | Implemented (optional) |
| Rules | shared rule list/inspect/explain/summary | Implemented |
| Evidence | provider list/inspect/capabilities/explain | Implemented |
| Architecture conclusions | policy + conclusion inspect/explain | Implemented |
| Architecture assessment | section/findings/conclusions/recommendations/coverage/limitations/traceability | Implemented |
| Resources | `codestrata://repositories…`, assessments findings/recommendations; enterprise URIs when configured | Implemented |
| Prompts | `review_repository`, `explain_modernization_plan`, `review_snapshot_changes` | Implemented |

Full registration: `interfaces/mcp/tools/register.py`, `resources/`, `prompts/`.

---

## 15. Agent Platform

### Maturity classification

**Implemented foundation / production-capable with limitations** for application agents; **partial / legacy overlay** for LLM tool agent relative to current enrichment path.

### Confirmed application agent components

| Component | Path | Role |
| --------- | ---- | ---- |
| `AgentOrchestrator` | `application/agents/orchestrator.py` | Multi-agent workflows |
| `DeterministicAgentPlanner` | `application/agents/planner.py` | Plans steps |
| `KnowledgeAgent` | `knowledge_agent.py` | Knowledge review |
| `AssessmentAgent` | `assessment_agent.py` | Calls assessment service |
| `ValidationAgent` | `validation_agent.py` | Validates persisted assessment |
| Factory / policies | `factory.py`, `policies.py` | Composition + bounds |

### Explicit answers

1. **Do agents execute?** Yes — via CLI/MCP orchestrator workflows.  
2. **Used in assessment pipeline?** No — not imported by `AssessmentApplicationService`; agents may *call* assess.  
3. **CLI?** Yes — `aimf agent {review,assess,validate,compare,modernization-review}`.  
4. **MCP?** Yes — `*_with_agents` tools.  
5. **Tool-calling?** Application agents: no LLM tools; AI stack: `AIMFToolRegistry` exists.  
6. **Memory / persistent agent context?** Not confirmed as conversational memory; they use knowledge-store DTOs.  
7. **Multi-agent orchestration?** Yes — Knowledge + Assessment + Validation under orchestrator.  
8. **Required for deterministic analysis?** No.  
9. **Before production-ready agents (LLM):** durable memory, clearer enrichment vs orchestrator ownership, stronger end-to-end agent tests — **Not confirmed** as fully complete.

No `AgentRegistry` class — agents are factory-composed.

---

## 16. CLI Platform

Root: `aimf` (`src/aimf/cli/__init__.py`, entry `aimf = "aimf.cli:app"`).

| Command group | Commands |
| ------------- | -------- |
| Root | `version`, `scan`, `assess` |
| `mcp` | `serve` |
| `agent` | `review`, `assess`, `validate`, `compare`, `modernization-review` |
| `incremental` | `plan`, `assess`, `explain` |
| `enterprise` | `init`, `validate`, `build`, `inspect`, `query`, `explain`, `compare` |
| `rules` | `list`, `inspect`, `explain` |
| `evidence` | `providers list|inspect|explain`, `capabilities`, `plan` |
| `architecture conclusions` | `policies`, `list`, `inspect`, `explain`, `plan` |
| `architecture assessment` | `inspect`, `findings`, `conclusions`, `recommendations`, `coverage`, `limitations`, `traceability` |

JSON output flags exist on many inspect commands. Config via `--config` / `aimf.toml`.

---

## 17. Configuration Platform

Owner: `AimfSettings` in `config/settings.py`; load via `load_settings`.

| Section | Owner | Notable defaults |
| ------- | ----- | ---------------- |
| `repository` | required | path/url/branch |
| `workspace` / `knowledge` | knowledge store | local SQLite workspace |
| `static_analysis` | PMD | `enabled=false` |
| `aws` / `ai` | Bedrock enrichment | model settings |
| `mcp` | MCP | `enabled=true`, `transport=stdio` |
| `agents` | Agent framework | `enabled=true` |
| `incremental` | Incremental | `enabled=false`, `execution_enabled=false` |
| `enterprise` | Enterprise KG | `enabled=false` |
| `rules` / `rules.architecture` | Shared rules / pack | both `enabled=false` |
| `evidence.language` | Language providers | `enabled=false` |
| `analysis.architecture_conclusions` | Conclusions | `enabled=false` |
| `assessment.sections.architecture` | Assessment section | `enabled=false` |

Feature fingerprints used by conclusions/assessment assembly. Unknown TOML keys: Pydantic validation behavior applies (extra handling per model).

---

## 18. Telemetry and Diagnostics

| Area | Implementation |
| ---- | -------------- |
| Rule / evidence / conclusion telemetry | Structured records on result objects (counts, durations, fingerprints, failures) |
| Architecture assessment | Section metadata + artifact byte size on write result |
| Logging | Application logging config; console stage messages in assess |
| External emission | **Not confirmed** as a remote telemetry backend |
| Persistence | Embedded in artifacts / knowledge AI docs; not a separate metrics store |
| Privacy | MCP/tools avoid dumping source; sanitization helpers in assess AI path |

Classification: **local / artifact-embedded / production-capable with limitations**.

---

## 19. Artifacts and Persistence

| Artifact | Writer | Deterministic | Gitignored |
| -------- | ------ | ------------- | ---------- |
| `findings.json` | `services/rule_engine/artifacts.py` | Yes (`dumps_stable_json`) | under `reports/` |
| `recommendations.json` | `services/recommendations/artifacts.py` | Yes | yes |
| `architecture_conclusions.json` | assess service inline | Mostly (model_dump_json) | yes |
| `architecture-assessment.json` | assessment artifacts writer | Yes + atomic replace | yes |
| `report.json` / `report.html` | reporting serialization | JSON stable; HTML render | yes |
| `graphs/*.json` | graph assessment artifacts | Yes | yes |
| `ai-enrichment.json` / `ai-execution.json` | AI/reporting | Yes | yes |
| Knowledge SQLite | infrastructure knowledge store | N/A | workspace gitignored |

`reports/` is gitignored (`.gitignore`).

---

## 20. Registries

| Registry | Location | Duplicate / version behavior |
| -------- | -------- | ---------------------------- |
| `RuleRegistry` | `application/rules/registry.py` | Rejects duplicates |
| `LanguageEvidenceProviderRegistry` | `application/evidence/language/registry.py` | Registry errors on conflict |
| `ArchitectureConclusionPolicyRegistry` | `application/architecture/conclusions/registry.py` | Duplicate + version conflict rejection |
| `AIMFToolRegistry` | `ai/tools/registry.py` | AI tool registration |
| `SqliteRepositoryRegistry` | `infrastructure/knowledge_store/…` | Knowledge identity |

MCP/CLI register functions are interface registration, not domain registries.  
**No AgentRegistry.**

---

## 21. Planners

| Planner | Location | Purpose |
| ------- | -------- | ------- |
| `RulePlanner` | `application/rules/planner.py` | Rule applicability/order |
| `LanguageEvidenceProviderPlanner` | `application/evidence/language/planner.py` | Provider plan |
| `DeterministicAgentPlanner` | `application/agents/planner.py` | Agent workflow steps |
| `IncrementalPlanner` | `application/incremental/planner.py` | Incremental assessment plan |

---

## 22. Executors and Orchestrators

| Name | Location | Notes |
| ---- | -------- | ----- |
| `RuleExecutor` | `application/rules/executor.py` | Per-rule execution |
| `LanguageEvidenceProviderExecutor` | `application/evidence/language/executor.py` | Provider isolation |
| `RuleExecutionFacade` | `application/rules/facade.py` | Legacy vs shared entry |
| `GraphAssessmentPipeline` | `services/graph_assessment/pipeline.py` | Graph build sequence |
| `KnowledgePipeline` | `services/knowledge_pipeline/pipeline.py` | Binding |
| `AssessmentApplicationService` | `application/assessment/service.py` | End-to-end assess |
| `AgentOrchestrator` | `application/agents/orchestrator.py` | Multi-agent |
| Incremental executors | `application/incremental/*execution*.py` | Opt-in |

Concurrency/retries: largely sequential; **Not confirmed** as a general retry framework.

---

## 23. Adapters and Bridges

| Adapter | Why it exists | Likely permanence |
| ------- | ------------- | ----------------- |
| `LegacyRuleAdapter` | Bridge Phase 3 rules to SharedRule | Temporary/compatibility until full migration |
| `RuleFindingMapper` | Platform matches → Finding | Intended |
| Language `legacy_adapter` / `architecture_adapter` | Compatibility + view building | Intended + transitional legacy path |
| `Phase1RepositoryAdapter` | Phase 1 repo → inventory inputs | Intended bridge |
| AI enrichment parsing bridges | Recommendation ↔ enrichment | Intended |
| CLI/MCP mapping modules | Interface DTOs | Intended |

---

## 24. Extension Model (supported today)

| Extension | Actual path |
| --------- | ----------- |
| Language provider | Implement provider → register in evidence factory/registry → config toggles |
| Shared rule | Implement `SharedRule` → register via pack registration / `RuleRegistry` |
| Rule pack | Follow `ArchitectureRulePack` + `register_architecture_pack` pattern (only one pack today) |
| Conclusion policy | Implement policy → `ArchitectureConclusionPolicyRegistry` / factory defaults |
| Assessment section | **Architecture-specific assembler today**; no generic section plugin API confirmed |
| CLI command | Register Typer command/group on `cli/__init__.py` `app` |
| MCP tool/resource | Add module + call from `register_all_tools` / resources |
| Agent | Extend orchestrator/factory (no registry) |
| Report section | Extend HTML v2 / assessment JSON builders (architecture section not hooked) |

---

## 25. Failure Isolation and Degradation

| Failure | Typical behavior |
| ------- | ---------------- |
| Unsupported language | Providers skip / not planned; legacy analyzers may still run |
| Provider failure | Evidence pipeline can continue others; architecture may fall back to legacy view builder |
| Graph failure | Assess aborts with `AssessmentCommandError` |
| Rule failure | Platform records failures; legacy engine errors abort rule stage |
| Conclusion policy failure | Isolated; other policies continue; diagnostics recorded |
| Architecture section | Built after findings; failures currently surface in rule stage exception boundary |
| Artifact write | Atomic replace for architecture-assessment/report writers |
| Report render | Assess error if validation/write fails |
| MCP handler | Bounded error mapping (`RuleApplicationError` / run_bounded) |
| Agent failure | Workflow-level error handling in orchestrator (see agent tests) |

---

## 26. Determinism and Reproducibility

| Mechanism | Present |
| --------- | ------- |
| Stable finding/conclusion/cluster IDs | Yes |
| Sorted JSON (`sort_keys`) | Yes for stable artifact helpers |
| Fingerprints (graph, config, providers) | Yes |
| Timestamps in report paths | Yes (run directory names) — intentional nondeterminism of path, not IDs |
| Caches | Local caches gitignored; incremental opt-in |
| Nondeterminism sources | Wall-clock run folders; AI enrichment content when enabled; filesystem iteration must be sorted (generally is) |

---

## 27. Security and Privacy Boundaries (implemented)

- Secret exclusion patterns in scanners/analyzers (Phase 1 security analyzer)
- MCP bounded responses; architecture tools avoid raw source
- Path display relativization in assess console
- Provider text sanitization for AI errors
- Credential references via env (`token_env`) for GitHub auth — not secrets in TOML

This is an inventory, not a security audit.

---

## 28. Test Architecture

Approximate test function counts (repo scan of `tests/**/test_*.py`): **~1110**.

| Area | Approx focus |
| ---- | ------------ |
| `tests/services` | ~246 |
| `tests/application` | ~220 (rules, evidence, architecture, agents, assessment, …) |
| `tests/ai` | ~195 |
| `tests/reporting` + `reporters` | ~121 |
| `tests/interfaces` | ~23 (MCP) |
| `tests/cli` + assess CLI | substantial |

High-risk thin areas (relative): full CLI×MCP×architecture assessment end-to-end matrices; positive evidence; multi-pack intelligence; report consumption of architecture sections (none yet).

---

## 29. Current Platform Maturity

| Subsystem | Status | Maturity |
| --------- | ------ | -------- |
| Repository analysis (Phase 1) | substantially complete | production-capable with limitations |
| Graph/knowledge pipeline | substantially complete | production-capable with limitations |
| Knowledge store | substantially complete | production-capable with limitations |
| Shared Rule Platform | substantially complete (infra) | production-capable with limitations |
| Language evidence | substantially complete | production-capable with limitations (disabled default) |
| Architecture Intelligence | substantially complete (through 4.2.4) | production-capable with limitations |
| Assessment orchestration | substantially complete | production-capable with limitations |
| Reporting (current HTML/JSON) | substantially complete | production-capable with limitations |
| MCP | substantially complete | production-capable with limitations |
| Application agents | partial / foundation+ | production-capable with limitations |
| AI enrichment | partial | production-capable with limitations |
| Other intelligence packs | planned / not found | documentation/roadmap only |
| CTO report architecture sections | substantially complete (4.2.5) | optional HTML/JSON section |

---

## 30. Confirmed Architectural Debt

| Debt | Evidence | Impact | Blocks packs? | Status after 4.2.5 |
| ---- | -------- | ------ | ------------- | ------------------ |
| Dual rule engines (legacy RuleEngine + Shared Rule Platform) | assess merges both | Cognitive/ops complexity | Soft | Still present |
| Architecture conclusions written inline vs formal artifact helper | `assessment/service.py` | Inconsistent artifact conventions | No | Still present |
| Report pipeline ignores architecture section/conclusions | resolved via adapter | Was blocking CTO presentation | — | **Addressed in 4.2.5** |
| Package/CLI name `aimf` vs product CodeStrata | `pyproject.toml`, CLI | Naming friction | No | Explicit non-goal |
| Assessment section model architecture-specific | `assessment.sections.architecture` only | Weak generic section framework | Soft for next packs | Still present |
| Positive evidence / strengths empty | conclusions + assessment | No positive architecture strengths | Soft | Still present |
| Agent vs enrichment ownership overlap | AI agent still referenced; enrichment preferred | Confusion | No | Document-only OK |
| Incomplete end-to-end tests for architecture assessment in assess | unit tests exist; limited assess E2E | Regression risk | Soft | Partially improved |

Do not treat debt as a mandate for redesign.

---

## 31. Current Gaps

### Product Capability Gaps
- Full CTO/executive report redesign (beyond architecture section)
- Additional intelligence packs (TD/Security/Performance/Modernization)
- Positive architecture strengths

### Platform Infrastructure Gaps
- Generic assessment-section plugin registry
- Unified artifact writer for conclusions
- Graph DB (intentionally absent)

### Intelligence Pack Gaps
- Only Architecture pack implemented

### Assessment Gaps
- Non-architecture sections
- Business impact remains unknown without enterprise context

### Report Gaps
- Architecture section not rendered
- Charts for architecture — not confirmed

### MCP Gaps
- No dedicated “generic assessment section” beyond architecture-focused tools

### Agent Gaps
- No agent registry; no durable conversational memory; LLM tool agent not central to assess

### Test Gaps
- Thin assess-enabled architecture section E2E; scanner sandbox flake on `.git/config`

### Documentation Gaps
- Older `docs/architecture/*.md` stubs vs this inventory; methodology docs may outpace packs

---

## 32. Recommended Next Step

### Recommendation: Architecture Intelligence substantially complete — choose next pack or CTO redesign

**Status:** Phase **4.2.5** integrates architecture assessment into `report.json` / HTML via `ArchitectureReportAdapter` (disabled by default; schema remains 1.2).

**Suggested next options:**
- Technical Debt Intelligence (4.3)
- Full CTO report redesign (assessment-framework target layout)
- Hardening: positive evidence, generic section pattern, architecture-enabled assess E2E

**What not to change without an explicit product decision:**
- Finding/conclusion IDs
- Disabled-by-default flags
- Package/CLI rename (`aimf`)
- Broad platform redesign
