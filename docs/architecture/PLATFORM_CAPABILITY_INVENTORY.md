# Platform Capability Inventory

Implementation-based operational inventory for CodeStrata (`aimf` package/CLI).  
Companion narrative: [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md).

**Legend — Status:** complete · substantially complete · partial · foundation only · experimental · planned · not found  

**Legend — Maturity:** production-ready · production-capable with limitations · internal beta · prototype · skeleton · documentation only

---

## Core Repository Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Local scan | `LocalRepositoryScanner` | substantially complete | `services/scanners/local_repository_scanner.py` | `tests/services/scanners/` | Sandbox may block `.git/config` write |
| GitHub scan | `GitHubRepositoryScanner` | substantially complete | `services/scanners/github_repository_scanner.py` | services tests | Auth via env refs |
| Inventory / manifest | `RepositoryInventoryBuilder` | substantially complete | `services/inventory/` | services/domain tests | Fingerprints |
| Technology detection | Composite detectors | substantially complete | `services/default_pipeline.py` | services | Java/JS/PHP detectors |
| Phase 1 analyzers | metrics, build, deps, CI/CD, security, architecture, cloud | substantially complete | `services/analyzers/` | `tests/services/analyzers/` | Not SharedRule packs |
| Static analysis (PMD) | `PmdProvider` | partial | `static_analysis/` | `tests/static_analysis/` | Disabled by default |
| Analysis result | `AnalysisService` → `AnalysisResult` | substantially complete | `services/analysis_service.py` | services | Phase 1 DTO |

---

## Graph and Knowledge Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Graph pipeline | `GraphAssessmentPipeline` | substantially complete | `services/graph_assessment/pipeline.py` | services | JSON artifacts, no graph DB |
| Repository graph | assemblers/extractors | substantially complete | `domain/repository_graph`, services | yes | `graphs/repository-graph.json` |
| Engineering knowledge | builtin catalog | substantially complete | `domain/engineering_knowledge` | yes | |
| Bindings | `KnowledgePipeline` | substantially complete | `services/knowledge_pipeline/` | yes | |
| Assessment graph | `AssessmentGraphBuilder` | substantially complete | `domain/assessment_graph` | yes | |
| Knowledge store | SQLite session/blobs | substantially complete | `infrastructure/knowledge_store/` | infrastructure tests | |
| Enterprise KG | YAML → file graph | substantially complete | `application/enterprise/`, `domain/enterprise/` | application/enterprise | Optional, disabled default |

---

## Shared Rule Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Rule contract | `SharedRule` | substantially complete | `domain/rules/contracts.py` | `tests/application/rules/` | |
| Registry / planner / executor | `RuleRegistry`, `RulePlanner`, `RuleExecutor` | substantially complete | `application/rules/` | Shared Rule Platform tests | |
| Facade / bridge | `RuleExecutionFacade`, `LegacyRuleAdapter` | substantially complete | `facade.py`, `legacy_adapter.py` | bridge tests | Dual path with legacy engine |
| Finding mapper | `RuleFindingMapper` | substantially complete | `finding_mapper.py` | yes | |
| Legacy RuleEngine | Phase 3 graph rules | substantially complete | `services/rule_engine/` | services | Still default in assess |
| CLI / MCP | `aimf rules`, shared-rule tools | substantially complete | `cli/rules.py`, `interfaces/mcp/tools/rules.py` | cli/mcp tests | |

---

## Evidence Provider Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Provider registry | `LanguageEvidenceProviderRegistry` | substantially complete | `application/evidence/language/registry.py` | evidence tests | |
| Planner / executor / aggregator | language evidence package | substantially complete | `planner.py`, `executor.py`, `aggregator.py` | yes | |
| Python/Java/JS providers | `language.*.core` @ 1.0.0 | substantially complete | `providers/` | yes | Disabled parent toggle |
| Architecture view adapter | `architecture_view_from_aggregated_evidence` | substantially complete | `architecture_adapter.py` | integration tests | |
| Legacy evidence adapter | `language.legacy.adapter` | partial | `legacy_adapter.py` | yes | Compatibility |
| CLI / MCP | `aimf evidence`, evidence tools | substantially complete | `cli/evidence.py`, MCP evidence tools | yes | |

---

## Architecture Intelligence

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Pack `architecture.core` 1.0.0 | 7 SharedRules | substantially complete | `application/rules/architecture/` | architecture rule tests | Assess opt-in |
| Precision hardening | unit selection, normalization, coverage split | substantially complete | view builder + rules | yes | 4.2.1a |
| Conclusions | policies + service | substantially complete | `application/architecture/conclusions/` | conclusion tests | Disabled default |
| Assessment section | assembler + artifact | substantially complete | `application/architecture/assessment/` | assessment section tests | Disabled default |
| Report rendering of section | `ArchitectureReportAdapter` + HTML/JSON | substantially complete | `reporting/architecture/` | architecture report tests | Disabled default |

---

## Assessment Framework

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Assess orchestration | `AssessmentApplicationService` | substantially complete | `application/assessment/service.py` | assess CLI / agents | |
| Findings / recommendations artifacts | writers | substantially complete | `services/*/artifacts.py` | yes | |
| Architecture section composition | optional | substantially complete | assessment service + assembler | unit tests | Not generic multi-section |
| Incremental assess | planner/executor | partial | `application/incremental/` | incremental tests | Opt-in |
| Customer report schema | JSON 1.2 | substantially complete | `reporting/assessment_json.py` | reporting tests | Optional `assessment.architecture` |

---

## Reporting Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| HTML v2 | builder/renderer | substantially complete | `reporting/html_v2/` | reporting tests | |
| `report.json` | schema 1.2 | substantially complete | `assessment_json.py` | yes | |
| Architecture section consumption | adapter + optional JSON/HTML | substantially complete | `reporting/architecture/` | yes | Disabled default |
| CTO executive layout | methodology docs | planned | `docs/assessment-framework/` | — | Not production UI |

---

## MCP Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Server | FastMCP CodeStrata | substantially complete | `interfaces/mcp/server.py` | `tests/interfaces/mcp/` | stdio only |
| Tool surface | 60+ tools across domains | substantially complete | `interfaces/mcp/tools/` | yes | |
| Resources | repository/assessment/enterprise URIs | substantially complete | `resources/` | yes | |
| Prompts | 3 prompts | substantially complete | `prompts/` | yes | |
| Bounds / no source dump | `run_bounded`, mapping | substantially complete | `_common.py`, mapping | yes | |

---

## Agent Platform

| Capability | Implementation | Status | Primary location | Tests | Notes |
| ---------- | -------------- | ------ | ---------------- | ----- | ----- |
| Application orchestrator | `AgentOrchestrator` | substantially complete | `application/agents/` | application/agents tests | Not inside assess pipeline |
| Knowledge/Assessment/Validation agents | dedicated classes | substantially complete | same | yes | |
| Deterministic planner | `DeterministicAgentPlanner` | substantially complete | `planner.py` | yes | |
| CLI / MCP exposure | `aimf agent`, `*_with_agents` | substantially complete | cli + MCP | yes | |
| LLM tool agent | `ModernizationAssessmentAgent` + `AIMFToolRegistry` | partial | `ai/agents/`, `ai/tools/` | ai tests | Enrichment preferred in assess |
| Agent registry / memory | — | not found | — | — | Factory composition only |

**Answers:** Agents execute (CLI/MCP). They do **not** participate inside deterministic assess orchestration. Multi-agent orchestration exists for application agents. Deterministic analysis does **not** require agents.

---

## CLI Platform

| Group | Commands | Status |
| ----- | -------- | ------ |
| Root | `version`, `scan`, `assess` | complete |
| `mcp` | `serve` | complete |
| `agent` | `review`, `assess`, `validate`, `compare`, `modernization-review` | complete |
| `incremental` | `plan`, `assess`, `explain` | complete |
| `enterprise` | `init`, `validate`, `build`, `inspect`, `query`, `explain`, `compare` | complete |
| `rules` | `list`, `inspect`, `explain` | complete |
| `evidence` | providers list/inspect/explain, capabilities, plan | complete |
| `architecture conclusions` | policies, list, inspect, explain, plan | complete |
| `architecture assessment` | inspect, findings, conclusions, recommendations, coverage, limitations, traceability | complete |

Registration: `src/aimf/cli/__init__.py`.

---

## Configuration

| Section | Default highlight | Owner |
| ------- | ----------------- | ----- |
| `repository` | required path/url | settings |
| `static_analysis.enabled` | false | settings |
| `rules.enabled` / `rules.architecture.enabled` | false / false | settings |
| `evidence.language.enabled` | false | settings |
| `analysis.architecture_conclusions.enabled` | false | settings |
| `assessment.sections.architecture.enabled` | false | settings |
| `incremental.enabled` / `execution_enabled` | false | settings |
| `enterprise.enabled` | false | settings |
| `mcp.enabled` | true | settings |
| `agents.enabled` | true | settings |

---

## Telemetry

| Area | Present | Persistence | External |
| ---- | ------- | ----------- | -------- |
| Rule/evidence/conclusion telemetry objects | yes | in artifacts/results | not confirmed |
| Assess console stages | yes | logs/console | local |
| Architecture assessment write metrics | yes | write result | local |

---

## Persistence and Artifacts

| Artifact | Schema / version | Deterministic writer | Consumer |
| -------- | ---------------- | -------------------- | -------- |
| `findings.json` | evaluation payload | yes | MCP/CLI/knowledge |
| `recommendations.json` | recommendation payload | yes | MCP/CLI/knowledge |
| `architecture_conclusions.json` | conclusion result | mostly | CLI/MCP inspect |
| `architecture-assessment.json` | section 1.0.0 | yes | CLI/MCP; **not** HTML |
| `report.json` | schema 1.2 | yes | customers |
| `report.html` | HTML v2 | render | customers |
| `graphs/*.json` | graph schemas 1.0.0 | yes | tools/knowledge |
| `ai-enrichment.json` / `ai-execution.json` | AI docs | yes | MCP artifacts |

All under gitignored `reports/` (and workspace dirs).

---

## Extension Points

| Extension | Supported path |
| --------- | -------------- |
| Language provider | registry + factory |
| Shared rule / architecture pack | `RuleRegistry` + pack registration |
| Conclusion policy | conclusion policy registry |
| Assessment section | architecture assembler only (no generic plugin API) |
| CLI / MCP | Typer / FastMCP registration |
| Agent | orchestrator factory (no registry) |
| Report section | HTML/JSON builders (manual) |

---

## Intelligence Packs

| Pack | Evidence | Rules | Conclusions | Assessment Section | Report Section | CLI | MCP | Status |
| ---- | -------- | ----- | ----------- | ------------------ | -------------- | --- | --- | ------ |
| Architecture | language providers + view builder | `architecture.core` 1.0.0 (7 rules) | yes (opt-in) | yes (opt-in) | **no** | rules/evidence/architecture | yes | substantially complete |
| Technical Debt | not found | not found | not found | not found | not found | category hint only | category hint | planned / not found |
| Security | Phase 1 analyzer only | no pack | no | no | partial Phase 1 in report | scan/assess | findings | foundation only |
| Performance | not found | not found | no | no | no | — | — | planned / not found |
| Cloud and Platform | Phase 1 cloud analyzer | no pack | no | no | Phase 1 facts | assess | — | foundation only |
| AI Readiness | not found as pack | not found | no | no | no | — | — | not found |
| Modernization | recommendations/phases | no MI pack | no | no | report phases | assess | recommendations | partial |

---

## Registry Inventory

| Registry | Location | Registers |
| -------- | -------- | --------- |
| `RuleRegistry` | `application/rules/registry.py` | SharedRules |
| `LanguageEvidenceProviderRegistry` | `application/evidence/language/registry.py` | Language providers |
| `ArchitectureConclusionPolicyRegistry` | `application/architecture/conclusions/registry.py` | Conclusion policies |
| `AIMFToolRegistry` | `ai/tools/registry.py` | AI analysis tools |
| `SqliteRepositoryRegistry` | `infrastructure/knowledge_store/…` | Repository identities |

---

## Planner Inventory

| Planner | Location |
| ------- | -------- |
| `RulePlanner` | `application/rules/planner.py` |
| `LanguageEvidenceProviderPlanner` | `application/evidence/language/planner.py` |
| `DeterministicAgentPlanner` | `application/agents/planner.py` |
| `IncrementalPlanner` | `application/incremental/planner.py` |

---

## Executor Inventory

| Executor / orchestrator | Location |
| ----------------------- | -------- |
| `RuleExecutor` | `application/rules/executor.py` |
| `LanguageEvidenceProviderExecutor` | `application/evidence/language/executor.py` |
| `RuleExecutionFacade` | `application/rules/facade.py` |
| `GraphAssessmentPipeline` | `services/graph_assessment/pipeline.py` |
| `AssessmentApplicationService` | `application/assessment/service.py` |
| `AgentOrchestrator` | `application/agents/orchestrator.py` |
| Incremental executors | `application/incremental/` |

---

## Artifact Inventory

See Persistence table above. Key filenames:

`findings.json`, `recommendations.json`, `architecture_conclusions.json`, `architecture-assessment.json`, `report.json`, `report.html`, `graphs/repository-manifest.json`, `graphs/repository-graph.json`, `graphs/engineering-knowledge-graph.json`, `graphs/knowledge-bindings.json`, `graphs/assessment-graph.json`, `graphs/graph-summary.json`, `ai-enrichment.json`, `ai-execution.json`.

---

## Current Feature Flags

| Flag path | Default |
| --------- | ------- |
| `static_analysis.enabled` | false |
| `rules.enabled` | false |
| `rules.architecture.enabled` | false |
| `evidence.language.enabled` | false |
| `analysis.architecture_conclusions.enabled` | false |
| `assessment.sections.architecture.enabled` | false |
| `incremental.enabled` | false |
| `incremental.execution_enabled` | false |
| `enterprise.enabled` | false |
| `mcp.enabled` | true |
| `agents.enabled` | true |
| `analysis.architecture_conclusions.policies.positive_boundary_conformance` | false |

---

## Disabled-by-Default Capabilities

- Shared Rule Platform execution in assess (via `rules.enabled`)
- Architecture pack merge
- Language evidence pipeline
- Architecture conclusions
- Architecture assessment section
- Incremental assessment execution
- Enterprise knowledge graph
- Static analysis (PMD)
- Positive boundary conformance conclusions

---

## Known Compatibility Layers

| Layer | Role |
| ----- | ---- |
| `LegacyRuleAdapter` / `RuleExecutionFacade.evaluate_adapted` | Phase 3 ↔ Shared Rule |
| Language `legacy_adapter` | Pre-provider collectors → evidence bundles |
| `Phase1RepositoryAdapter` | Phase 1 repository → inventory inputs |
| AI enrichment ↔ recommendation bridges | Enrichment mapping |
| Package name `aimf` vs product CodeStrata | Branding vs implementation |

---

## Known Gaps

- Non-architecture intelligence packs
- Generic assessment-section framework
- Positive architecture strengths/evidence
- Agent conversational memory / agent registry
- Conclusions artifact writer consistency vs other artifacts
- Thin E2E assess tests with architecture flags enabled
- Full CTO report redesign (beyond architecture section)

---

## Recommended Next Milestone

Architecture Intelligence (4.2) is substantially complete after 4.2.5.

Next product work should choose among:

- Technical Debt Intelligence (4.3)
- Security / Performance / Modernization packs
- Full CTO report redesign (assessment-framework target layout)
- Hardening: positive evidence, generic section pattern, E2E architecture assess coverage

Do not treat the overall CodeStrata product as complete.
