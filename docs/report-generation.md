# Report generation

Customer-facing CodeStrata Engineering Assessment (HTML) and companion JSON.

```text
ModernizationReportInput
        │  (+ Phase 3 findings / recommendations / optional AI)
        ▼
build_html_report_view_model()
        ▼
HtmlReportViewModel
        ▼
HtmlReportRenderer.render()
        ▼
report.html (self-contained, branded)
```

## Artifacts

| File | Role |
| ---- | ---- |
| `report.html` | CodeStrata Engineering Assessment |
| `report.json` | Machine-readable Phase 1 assessment contract |
| `findings.json` | Deterministic findings (unchanged by HTML) |
| `recommendations.json` | Deterministic recommendations |
| `ai-enrichment.json` | Optional AI narrative |

## Sections (HTML)

1. Hero dashboard (brand, repository, factual KPIs, mode)
2. Executive Summary (factual cards)
3. Technology Overview (badges + version highlights)
4. Findings Overview (severity meters + priority findings)
5. Modernization Roadmap (Immediate / Near Term / Future)
6. AI Executive Summary (only when enrichment is present)
7. Technical Details (repository, evidence, artifacts, metadata)

## Executive dashboard cards

Factual, evidence-backed values only (no composite “health” or “readiness” scores):

| Card | Source | Display |
| ---- | ------ | ------- |
| Files | Repository file count | integer |
| Technologies | Detected technologies | integer |
| Findings | Phase 3 / Phase 1 findings count | integer |
| Recommendations | Recommendation count | integer |
| Test Files Detected | `StructureFacts.test_file_count` / `has_tests` | count, Detected, Not detected, or Unknown |
| CI/CD | `CicdFacts.has_ci` / `pipeline_count` | Detected, Not detected, or Unknown |
| Cloud Enablement Signals | Seven cloud flags | `N of 7` + Established / Partial / Not detected, or Unknown |
| Repository Size | File count | `N files` |
| Highest Finding Severity | Max finding severity | Critical…Informational, None Detected, or Unknown |

Cloud signals counted: Docker, Kubernetes, Helm, Terraform, CloudFormation, Serverless, Docker Compose.

## Boundaries

* Renderer performs HTML/CSS only — no analysis re-run
* Must not invent or rewrite findings/recommendations
* Absolute host paths are not leaked into customer HTML
* JSON artifact contracts are unchanged by presentation redesign
* `ModernizationHTMLReportRenderer` is a thin facade over this renderer

See also [architecture/html-report-v2.md](architecture/html-report-v2.md).
