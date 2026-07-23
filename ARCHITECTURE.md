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
| Application | `AssessmentApplicationService` orchestration; knowledge ports/session |
| CLI | Config, thin adapters, artifact retention |

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
fails the assessment; incomplete runs are never “latest completed.” Full
recomputation only — no incremental execution yet.

Details: [docs/knowledge-store.md](docs/knowledge-store.md).

## Repository authentication

Private GitHub access uses credential **references** in config (`token_env`),
never secret values in TOML. Runtime credentials stay out of domain models and
reports. Authentication applies only to remote clones.

## Package layout (simplified)

```text
src/aimf/
├── cli/                 # Typer: version, scan, assess
├── config/
├── application/         # assessment orchestration; knowledge ports/session
├── infrastructure/      # SQLite knowledge store, blobs, Git revision observer
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
