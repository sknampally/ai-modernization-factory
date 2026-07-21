# AI Modernization Factory (AIMF) Architecture

## Purpose

AI Modernization Factory (AIMF) analyzes enterprise application repositories and produces evidence-based modernization assessments.

AIMF first performs deterministic analysis to discover technologies, build systems, dependencies, CI/CD configuration, and related repository characteristics. Structured facts and findings are the primary output today. AI interpretation of those facts is a planned later layer.

## Engineering Philosophy

> **Deterministic analysis first. AI reasoning second.**

Large language models are useful for reasoning over structured information, but less reliable at inventing facts from large codebases.

Instead of asking an LLM to “analyze this repository,” AIMF aims to ask:

> Here is everything we discovered about this application. Based on these facts, what modernization strategy would you recommend?

Benefits:

* Repeatable analysis
* Explainable findings
* Lower hallucination risk
* Lower token cost when AI is added
* Easier unit testing
* Clear separation between facts and interpretation

## Design Principles

### Separation of responsibilities

| Layer | Responsibility |
| ----- | -------------- |
| Scanners | Acquire source and inventory files |
| Detectors | Identify languages, frameworks, and tools |
| Analyzers | Produce facts and findings |
| CompositeAnalyzer | Run analyzers sequentially and merge facts |
| StaticAnalysisService | Orchestrate external providers (for example PMD) |
| AnalysisService | Orchestrate detection + native analysis + providers |
| Reporters | Present `AnalysisResult` |
| CLI | Load config, invoke pipeline, write output |

### Composable components

New scanners, detectors, analyzers, and reporters can be added without rewriting the orchestration layer. Analyzers implement a shared protocol and return deltas; the composite merges them.

### Evidence-based findings

Findings include title, description, category, severity, source, and structured evidence (file paths and supporting details). Recommendations, when added, must remain traceable to findings.

## Runtime Pipeline

```text
                    aimf.toml
                        │
                        ▼
                      CLI
                        │
                        ▼
             GitHubRepositoryScanner
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
 detection              │              ├── PMD
          │             ▼              └── Future providers
          │      facts + findings             │
          │             │                     ▼
          │             │            normalized findings
          └─────────────┴─────────────┬───────┘
                                      ▼
                           Recommendation engine
                                      ▼
                              AnalysisResult
                                      │
                        ┌─────────────┼─────────────┐
                        ▼             ▼             ▼
                   report.txt    report.json   report.html
```

### Provider boundary

AIMF owns:

* provider orchestration and availability checks
* normalization into `Finding` / `Evidence`
* modernization interpretation and recommendations
* reporting and baseline comparison

PMD owns:

* Java language rules
* source-level issue detection

### Adding a future provider

1. Implement `StaticAnalysisProvider` (`provider_id`, applicability, availability, `analyze`)
2. Normalize tool output into AIMF `Finding` objects with `FindingSource.EXTERNAL_STATIC_ANALYSIS`
3. Register the provider in the CLI when its config section is enabled
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

This allows later analyzers (for example dependency health) to consume earlier discovery/metadata facts.

Default analyzer order in the CLI:

1. `RepositoryMetricsAnalyzer`
2. `BuildDiscoveryAnalyzer`
3. `BuildMetadataAnalyzer`
4. `DependencyDiscoveryAnalyzer`
5. `DependencyMetadataAnalyzer`
6. `DependencyHealthAnalyzer`
7. `CicdDiscoveryAnalyzer`

## Package Layout

```text
src/aimf/
├── cli.py
├── config/
│   └── settings.py
├── repository_auth/
│   ├── models.py
│   ├── service.py
│   ├── providers/
│   └── ...
├── security/
│   └── redaction.py
├── models/
├── reporters/
├── static_analysis/
└── services/
    ├── analysis_service.py
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

Supporting parsers:

* `maven_dependency_parser.py` / `maven_version_resolver.py`
* `github_actions_parser.py` (GitHub Actions YAML parsing; available for deeper CI metadata)

### Domain models

`RepositoryFacts` aggregates:

* `build: BuildFacts | None`
* `dependencies: DependencyFacts | None`
* `cicd: CicdFacts | None`

`AnalysisResult` includes repository, technologies, facts, findings, recommendations (currently empty), and run metadata.

`AnalyzerResult` is the per-analyzer return value: findings plus newly produced facts.

### Reporters

* `TextFileReporter` / `JsonFileReporter` — write `report.txt` and `report.json`
* `ConsoleReporter` — summary or detailed terminal output
* Reports land in `reports/<repo>/<YYYYMMDD-HHMMSS>/` by default
* Only the latest 3 timestamped run directories are retained per repository

## Contracts

Key protocols in `services/contracts.py`:

* `TechnologyDetector.detect(repository) -> list[Technology]`
* `Analyzer.analyze(repository, technologies, facts=None) -> AnalyzerResult`

Analyzers should return only facts they produce. They must not echo the full accumulated facts; merging is the composite’s job.

## Current Status

### Completed

* Project packaging and CLI (`aimf version`, `aimf scan`)
* Config loading
* Local and GitHub scanning
* Technology detection (Java / JS / PHP)
* Analysis orchestration
* Build, dependency, metrics, and CI/CD discovery analyzers
* Dependency health findings
* Fact-merging composite pipeline
* Console and file reporters
* Automated tests and static analysis

### Next milestones

* Wire deeper CI/CD metadata parsing into the main pipeline
* Expand deterministic rule packs (security, quality, testing)
* Recommendation engine over findings
* AI interpretation of structured facts/findings
* Broader language and repository-source support

## Long-Term Vision

AIMF is intended to grow into a modular enterprise modernization platform covering:

* Repository and architecture assessment
* Technical debt and dependency risk analysis
* Cloud and AI readiness
* Modernization roadmaps and executive reporting
* Assisted refactoring and continuous monitoring

New capabilities should plug into the existing scan → detect → analyze → report flow without breaking deterministic guarantees.
