# AI Modernization Factory (AIMF) Architecture

## Purpose

AI Modernization Factory (AIMF) analyzes enterprise application repositories and produces evidence-based modernization assessments.

AIMF first performs deterministic analysis to discover technologies, build systems, dependencies, CI/CD configuration, architecture, security, and cloud-readiness characteristics. Structured facts, findings, and deterministic recommendations are the primary product. Optional AI interpretation runs over a budgeted, normalized evidence contract and augments the same HTML/JSON assessment report.

## Engineering Philosophy

> **Deterministic analysis first. AI reasoning second.**

Large language models are useful for reasoning over structured information, but less reliable at inventing facts from large codebases.

Instead of asking an LLM to “analyze this repository,” AIMF asks:

> Here is everything we discovered about this application. Based on these facts, what modernization strategy would you recommend?

Benefits:

* Repeatable analysis
* Explainable findings
* Lower hallucination risk
* Lower token cost (budgeted normalized context, not raw repositories or all PMD observations)
* Easier unit testing
* Clear separation between facts and interpretation
* Deterministic usefulness when AI is unavailable or fails

## Design Principles

### Separation of responsibilities

| Layer | Responsibility |
| ----- | -------------- |
| Scanners | Acquire source and inventory files |
| Detectors | Identify languages, frameworks, and tools |
| Analyzers | Produce facts and findings |
| CompositeAnalyzer | Run analyzers sequentially and merge facts |
| StaticAnalysisService | Orchestrate external providers (PMD today) |
| RecommendationEngine | Deterministic recommendations from findings |
| AnalysisService | Orchestrate detection + native analysis + providers + recommendations |
| AI contracts / prompts / providers / agents | Build budgeted context, invoke model once, validate output |
| Reporters (`reporters/`) | Present `AnalysisResult` for `aimf scan` |
| Reporting (`reporting/`) | Customer assess HTML/JSON modernization reports |
| CLI | Load config, invoke pipeline, write output |

### Composable components

New scanners, detectors, analyzers, providers, and reporters can be added without rewriting the orchestration layer. Analyzers implement a shared protocol and return deltas; the composite merges them.

### Evidence-based findings

Findings include title, description, category, severity, source, and structured evidence (file paths and supporting details). Deterministic and AI recommendations remain traceable to finding and group IDs.

## Runtime Pipelines

### Shared analysis

```text
                    aimf.toml / CLI flags
                        │
                        ▼
                      CLI
                        │
                        ▼
             Local or GitHub scanner
                        │
                        ▼
                   Repository
                        │
                        ▼
                 AnalysisService
                        │
          ┌─────────────┼─────────────────────┐
          ▼             ▼                     ▼
 Technology      CompositeAnalyzer   StaticAnalysisService
 detection              │              └── PMD (profiles)
          │             ▼                     │
          │      facts + findings             ▼
          │             │            normalize → group → visibility
          └─────────────┴─────────────┬───────┘
                                      ▼
                           Recommendation engine
                                      ▼
                              AnalysisResult
```

### `aimf scan` reporting

```text
AnalysisResult
    │
    ├─ report.txt
    ├─ report.json
    └─ report.html
         │
         ▼
 retain latest 3 runs (delete older)
```

### `aimf assess` reporting

```text
AnalysisResult
    │
    ├─ (deterministic mode) skip AI
    └─ (AI mode)
         ├─ LLMAnalysisContextBuilder + token budget
         ├─ exactly one Bedrock invocation
         └─ AIRecommendationResult validation
    │
    ▼
ModernizationReportInput
    │
    ├─ report.html   (deterministic sections first; AI section appended)
    └─ report.json   (schema/report version 1.2)
         │
         ▼
 prune older completed runs (keep latest 3 per repository; delete older)
```

AI failure behavior:

* Deterministic HTML and JSON are still written
* `assessment.ai.status = failed` with a sanitized warning
* No fabricated AI sections; prompts and raw responses are not exposed
* Retention still runs after successful artifact generation

### Provider boundary

AIMF owns:

* provider orchestration and availability checks
* PMD profile selection and command construction isolation
* normalization into observations, groups, and customer `Finding` objects
* modernization interpretation and recommendations
* reporting and baseline comparison

PMD owns:

* Java language rules
* source-level issue detection

### PMD normalization pipeline

```text
PMD XML report
    │
    ▼
parser (namespace-aware)
    │
    ▼
observations (raw; retained in JSON)
    │
    ▼
rule mapping + visibility + modernization relevance
    │
    ▼
grouping by remediation pattern
    │
    ▼
customer Finding cards (HTML) + grouped evidence
```

Profiles:

| Profile | Role |
| ------- | ---- |
| `focused` | Executive/customer assessment with lower stylistic noise |
| `standard` | Default modernization assessment |
| `comprehensive` | Broader evidence including lower-priority conventions |

Visibility: `primary` · `supporting` · `informational` · `suppressed_from_html`  
Critical/high findings are never suppressed from HTML.

### Adding a future provider

1. Implement `StaticAnalysisProvider` (`provider_id`, applicability, availability, `analyze`)
2. Normalize tool output into AIMF observations/groups/`Finding` objects with `FindingSource.EXTERNAL_STATIC_ANALYSIS`
3. Register the provider in the default pipeline when its config section is enabled
4. Keep command construction and parsing isolated from `AnalysisService`

### Repository authentication trust boundary

Private GitHub access uses a provider-neutral authentication boundary:

```text
Configuration reference
        ↓
RepositoryAuthenticationService
        ↓
Credential provider
        ↓
Runtime-only credential
        ↓
Scoped Git execution context
        ↓
Git clone
        ↓
Cleanup and redaction
```

Trust rules:

* AIMF configuration contains credential references only (`token_env`), never secret values
* Runtime credentials never enter analysis-domain models, reports, or baselines
* Git subprocess authentication is scoped to a single clone operation via `GIT_ASKPASS`
* Shared redaction (`aimf.security.redaction`) is defense-in-depth for operational output
* Future hosted deployments should use short-lived GitHub App installation tokens
* Future AWS-hosted deployments may resolve references through AWS Secrets Manager
* Those future capabilities are not implemented in this milestone

Authentication applies only to remote GitHub cloning. Local repository scanning ignores authentication configuration.

### Analyzer fact pipeline

`CompositeAnalyzer` runs analyzers in order:

1. Pass accumulated `RepositoryFacts` into the analyzer
2. Receive new findings and newly produced facts (a delta)
3. Merge the delta into the accumulated facts
4. Pass the merged facts to the next analyzer

Default analyzer order:

1. `RepositoryMetricsAnalyzer`
2. `BuildDiscoveryAnalyzer`
3. `BuildMetadataAnalyzer`
4. `DependencyDiscoveryAnalyzer`
5. `DependencyMetadataAnalyzer`
6. `DependencyHealthAnalyzer`
7. `CicdDiscoveryAnalyzer`
8. `SecurityAnalyzer`
9. `ArchitectureAnalyzer`
10. `CloudReadinessAnalyzer`

### AI assessment architecture

```text
AnalysisResult
    │
    ▼
LLMAnalysisContextBuilder
    ├─ facts summary (compact; no full dependency lists)
    ├─ static-analysis profile + counts
    ├─ deterministic recommendations
    └─ prioritized finding selection (budget.py)
         │
         ▼
ModernizationPromptBuilder
         │
         ▼
create_bedrock_runtime_client()   # single Bedrock Runtime client factory
         │                         # aws.profile / aws.region → env → boto3 chain
         ▼
BedrockAIModelProvider.converse()  (exactly one Converse call; model-family neutral)
         │
         ▼
AIRecommendationResult
         │
         ▼
validate_recommendation_result
    ├─ AI-REC-001… sequential IDs (not PMD / DET / REC-* IDs)
    ├─ 5–8 recommendations for evidence-rich assessments
    ├─ related_finding_ids → findings only; related_deterministic_recommendation_ids for DET IDs
    ├─ 2–4 non-empty phases; every AI-REC in exactly one phase
    ├─ reject unsupported severity escalation and invented paths
    └─ recompute evidence_coverage from unique related_finding_ids
       (model-supplied coverage arithmetic is untrusted and overwritten)
         │
         ▼
ModernizationAssessmentResult → reporting layer
```

AI context budget priority:

1. Critical/high native AIMF findings
2. Critical/high primary PMD groups
3. Medium primary PMD groups
4. Medium supporting PMD groups
5. Deterministic recommendations / architecture-security-cloud-build facts
6. Low/informational findings only when space remains

Never truncate finding IDs, severity, category, or critical/high evidence. If critical/high evidence cannot fit, fail clearly (`AIContextBudgetError`) rather than silently dropping it.

Budget metadata recorded on the context and mirrored into JSON:

* `candidate_finding_count`
* `included_finding_count`
* `omitted_informational_count`
* `estimated_input_tokens`
* `static_analysis_profile`

Provider token usage and latency are recorded when the model returns them.

## Package Layout

```text
src/aimf/
├── cli/
│   ├── __init__.py          # Typer app: version, scan, assess
│   └── assess.py            # assess command + AI orchestration
├── config/
│   └── settings.py
├── repository_auth/
├── security/
│   └── redaction.py
├── models/
├── reporters/               # scan reporters + shared HTML helpers
├── reporting/               # assess modernization HTML/JSON
│   ├── assessment_json.py
│   ├── modernization_html.py
│   ├── modernization_models.py
│   └── ...
├── ai/
│   ├── aws_config.py        # centralized AWS profile/region + Bedrock client
│   ├── contracts/           # LLMAnalysisContext + budgeted builder
│   ├── prompts/
│   ├── providers/           # Bedrock + parsing
│   ├── agents/              # modernization assessment agent
│   ├── recommendations/     # typed AI result + validation
│   └── tools/               # optional analysis tools for agents
├── static_analysis/
│   ├── service.py
│   ├── grouping.py
│   ├── visibility.py
│   └── providers/           # PMD command/parser/profiles/normalization
└── services/
    ├── analysis_service.py
    ├── default_pipeline.py
    ├── recommendation_engine.py
    ├── scan_comparison_service.py
    ├── analyzers/
    ├── detectors/
    └── scanners/
```

## Component Details

### Configuration

`aimf.toml` is loaded into Pydantic settings:

* `repository.url` — GitHub HTTPS or SSH URL
* `repository.branch` — optional branch
* `repository.authentication` — optional credential reference (`github_token` or `ssh_agent`)
* `workspace.directory` — clone workspace
* `workspace.clean_before_clone` — whether to replace an existing clone
* `static_analysis.enabled` / `fail_on_provider_error`
* `static_analysis.pmd.*` — executable, profile, rulesets, priority, timeout
* `aws.profile` / `aws.region` — optional AWS session for Bedrock (preferred over exporting env vars)
* `ai.provider` — AI provider name (currently `bedrock`)
* `ai.bedrock.model_id` — Bedrock model ID (defaults to `amazon.nova-lite-v1:0` when unset)
* `ai.bedrock.region` — optional legacy region fallback

### Scanners

* `LocalRepositoryScanner` — walks a local tree and collects relative file paths
* `GitHubRepositoryScanner` — shallow-clones a GitHub repo (public or authenticated private), then uses the local scanner

### Technology detectors

`CompositeTechnologyDetector` combines:

* `JavaTechnologyDetector`
* `JavaScriptTechnologyDetector`
* `PhpTechnologyDetector`

### Analyzers

| Analyzer | Produces |
| -------- | -------- |
| `RepositoryMetricsAnalyzer` | Structural metrics findings |
| `BuildDiscoveryAnalyzer` | `BuildFacts` (systems, wrappers, lockfiles) |
| `BuildMetadataAnalyzer` | Richer `BuildFacts` (modules, packaging, Java versions, commands) |
| `DependencyDiscoveryAnalyzer` | Dependency manifests / lockfiles |
| `DependencyMetadataAnalyzer` | Parsed direct dependencies and categories |
| `DependencyHealthAnalyzer` | Findings such as unmanaged/dynamic versions and missing lockfiles |
| `CicdDiscoveryAnalyzer` | `CicdFacts` for detected pipeline files |
| `SecurityAnalyzer` | Security-oriented facts and findings |
| `ArchitectureAnalyzer` | Architecture facts and layering/design findings |
| `CloudReadinessAnalyzer` | Cloud-readiness facts and findings |

Supporting parsers:

* `maven_dependency_parser.py` / `maven_version_resolver.py`
* `github_actions_parser.py` / `yaml_pipeline_loader.py`

### Domain models

`RepositoryFacts` aggregates structure, technology, build, dependencies, CI/CD, security, architecture, and cloud facts.

`AnalysisResult` includes repository, technologies, facts, findings, deterministic recommendations, static-analysis results (observations + groups + counts), optional comparison metadata, and run metadata.

`StaticAnalysisResult` retains:

* raw `observations` (JSON)
* `groups` and customer-facing `findings`
* profile, files analyzed, visibility counts

### Deterministic recommendations

`RecommendationEngine` derives modernization recommendations from findings (including at most one deterministic recommendation per high-value PMD group). Recommendations remain in JSON unchanged when AI runs. HTML groups related deterministic recommendations by category for executive readability and keeps them separate from AI recommendations.

### Reporters vs reporting

| Path | Used by | Artifacts | Retention |
| ---- | ------- | --------- | --------- |
| `reporters/` | `aimf scan` | `report.txt`, `report.json`, `report.html` | Keep latest 3 completed runs (delete older) |
| `reporting/` | `aimf assess` | `report.html`, `report.json` only | Keep latest 3 completed runs (delete older; no archive/) |

Assess HTML structure (high level):

1. Executive summary and repository system intelligence
2. Static analysis summary
3. Deterministic findings
4. Deterministic recommendations
5. Optional comparison section
6. AI interpretation (`not_requested`, `succeeded`, or an explicit failure status such as `validation_failed`)
7. Coverage, execution metadata, methodology

When AI was requested but the response fails validation after a successful provider call, reports show deterministic fallback (not “AI not executed”), retain provider/token metadata, and may write developer-only `ai-response-diagnostic.json` in the run directory. Unvalidated AI content is never included in customer-facing HTML/JSON.

### AI contracts

* `LLMAnalysisContext` schema version **1.1.0**
* `AIRecommendationResult` schema version **1.0.0**
* Assessment JSON schema/report version **1.2**

Assess JSON AI block includes execution status, lifecycle stages, provider/model, executive summary, key risks, recommendations, phases, limitations, evidence coverage, token usage, latency, failure code/detail when applicable, and budget metadata. HTML and JSON must agree on AI status, counts, provider/model, tokens, latency, and evidence references. A successful provider call that later fails contract validation is reported as `validation_failed` (with metadata preserved), not as `executed: false` without invocation context.

## Contracts

Key protocols:

* `TechnologyDetector.detect(repository) -> list[Technology]`
* `Analyzer.analyze(repository, technologies, facts=None) -> AnalyzerResult`
* `StaticAnalysisProvider.analyze(context) -> StaticAnalysisResult`
* `AIModelProvider.invoke(...) -> ModelInvocationResult`

Analyzers should return only facts they produce. They must not echo the full accumulated facts; merging is the composite’s job.

## Current Status

### Completed

* Project packaging and CLI (`aimf version`, `aimf scan`, `aimf assess`)
* Config loading and private GitHub authentication boundary
* Local and GitHub scanning
* Technology detection (Java / JS / PHP)
* Analysis orchestration with fact-merging composite pipeline
* Build, dependency, metrics, CI/CD, security, architecture, and cloud analyzers
* Deterministic recommendation engine
* PMD provider with profiles, namespace-aware parsing, normalization, grouping, and visibility
* Scan reporters (text/JSON/HTML) and assess modernization reports (HTML/JSON)
* Assess report retention (latest 3 completed runs per repository; no local archive)
* Baseline scan comparison
* AI evidence contract, token budgeting, Bedrock provider, prompt builder, assessment agent, and output validation
* Failure-safe AI mode that retains deterministic reports
* Automated tests and static analysis (pytest / Ruff / MyPy)

### Next milestones

* Additional static-analysis providers (SonarQube / Semgrep / CodeQL)
* Richer structured AI risk objects (beyond string titles + high-priority recommendation cards)
* Broader language and repository-source support
* Assisted refactoring and continuous modernization workflows

## Long-Term Vision

AIMF is intended to grow into a modular enterprise modernization platform covering:

* Repository and architecture assessment
* Technical debt and dependency risk analysis
* Cloud and AI readiness
* Modernization roadmaps and executive reporting
* Assisted refactoring and continuous monitoring

New capabilities should plug into the existing scan → detect → analyze → (optional AI) → report flow without breaking deterministic guarantees.
