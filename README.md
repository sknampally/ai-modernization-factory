# AI Modernization Factory (AIMF)

**Version:** 0.1.0 · **License:** MIT

AIMF analyzes application repositories and produces evidence-based modernization
assessments. Deterministic analysis is the source of truth. Optional AI
enrichment adds a concise narrative—never inventing findings or recommendations.

> **Deterministic analysis first. AI reasoning second.**

---

## What is AIMF?

AIMF (AI Modernization Factory) is a Python CLI that:

1. Scans a local or GitHub repository
2. Detects technologies and extracts structural facts
3. Builds knowledge graphs (repository, engineering knowledge, assessment)
4. Runs deterministic rules → findings → recommendations
5. Optionally calls Amazon Bedrock **once** for narrative enrichment
6. Writes self-contained HTML Report v2 plus machine-readable JSON artifacts

Use it for modernization discovery, client demos, and engineering due diligence.

---

## Features

* Local path and public/private GitHub repository assessment
* Technology detection for **Java**, **JavaScript/TypeScript**, and **PHP**
* Repository Inventory → Repository Graph → Assessment Graph pipeline
* Dependency and version extraction (Maven / npm)
* Deterministic Rule Engine and Recommendation Engine
* Optional one-call Bedrock AI enrichment with ID traceability
* Self-contained **HTML Report v2** (no CDN)
* JSON artifacts for findings, recommendations, graphs, and enrichment
* Deterministic mode (zero AI calls) and AI mode (exactly one call)
* Optional PMD static analysis for Java
* Durable knowledge store (`.aimf/knowledge`) with query services
* Local **CodeStrata** FastMCP server (`aimf mcp serve`)
* Deterministic **Agent Framework** (`aimf.application.agents`) over application services
* Thin **`aimf agent`** CLI and high-level MCP agent tools over `AgentOrchestrator`
* Incremental assessment with validation, telemetry, explainability, and opt-in CLI/MCP (`aimf.application.incremental`; `rollout_mode=off` by default)
* Enterprise Knowledge Graph from YAML (`aimf enterprise`; optional, disabled by default)
* Shared Rule Platform (`aimf rules`; Phase 4.1 infrastructure; disabled by default)
* Assessment Framework methodology (Phase 4.1.2; docs only — scoring/CTO report not wired)
* Architecture Intelligence initial pack (`architecture.core` v1.0.0; Phase 4.2.1 / 4.2.1a; discoverable via `aimf rules list --category architecture`; assess merge opt-in)
* Language Evidence Provider Foundation (Phase 4.2.2; `aimf evidence`; disabled by default)
* Architecture Conclusions (Phase 4.2.3; `aimf architecture conclusions`; disabled by default)
* Architecture Assessment Integration (Phase 4.2.4; `architecture-assessment.json`; disabled by default)
* Architecture CTO Report Integration (Phase 4.2.5; optional `assessment.architecture` in `report.json` / HTML; disabled by default)
* Technical Debt Domain Foundation (Phase 4.3.1; assessment contracts + feature gates; disabled by default)
* Complexity Evidence (Phase 4.3.2; Python/Java structural metrics via Language Evidence Platform)
* Technical Debt Complexity Rules (Phase 4.3.3; `technical_debt.core` SharedRules; pack disabled by default)
* Technical Debt Complexity Assessment Vertical (Phase 4.3.4 / 4.3.4A; assess opt-in; production-primary inventory + hotspots; dogfood accepted)
* Technical Debt conclusions / CTO report integration (deferred; Phase 4.3.5–4.3.6)

---

## Architecture

```text
                    aimf.toml / CLI
                           │
                           ▼
              Local path or GitHub clone
                           │
                           ▼
              Phase 1 analysis (detect + analyzers)
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
     Deterministic HTML/JSON    optional AI enrichment
        (report.html v2)         (one Bedrock call)
                                        │
                                        ▼
                                 ai-enrichment.json
```

Deeper design notes: [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/](docs/).

---

## Installation

Requires **Python 3.12+**.

Cloning the repository does **not** install the `aimf` command. If you see
`ModuleNotFoundError: No module named 'aimf'`, create a venv and install the
package editable from the repo root:

```bash
git clone https://github.com/sknampally/ai-modernization-factory.git
cd ai-modernization-factory

python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
# optional Bedrock + tests:
python -m pip install -e ".[dev]"
```

Verify the install points at this checkout:

```bash
python -c "import aimf; print(aimf.__file__)"
aimf version
aimf assess --help
```

---

## Quick Start (local repo)

```bash
# Bundled sample app
aimf assess --repo examples/sample-js-app --output reports

# Or your checkout
aimf assess --repo /path/to/your-app --output reports
```

Open the newest `reports/<repo-name>/<timestamp>/report.html`.

Config-driven equivalent (default `aimf.toml` points at the sample app):

```bash
aimf assess --config aimf.toml --output reports
```

---

## Quick Start (GitHub repo)

```toml
# aimf.toml
[repository]
url = "https://github.com/YOUR_ORG/YOUR_REPO"
branch = "main"
```

```bash
aimf assess --config aimf.toml --output reports
```

Private HTTPS repos: set a token in `.env` (never commit secrets) and reference
it from config—see [examples/README.md](examples/README.md).

---

## AI mode

Deterministic mode is the default (`--no-ai`). AI mode requires AWS credentials
that can call Bedrock, plus a model ID:

```bash
aws sso login --profile <profile-name>
aimf assess --config aimf.toml --output reports --with-ai
```

Configure profile/region/model in `aimf.toml`:

```toml
[aws]
profile = "<profile-name>"
region = "us-east-1"

[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"
```

| Mode | Provider calls | Enrichment artifact |
| ---- | -------------- | ------------------- |
| Deterministic | 0 | none |
| `--with-ai` | exactly 1 | `ai-enrichment.json` on success |

If AI fails, deterministic reports and graphs are kept; the CLI completes with a
warning (exit 0). AI never modifies `findings.json` or `recommendations.json`.

---

## Output artifacts

```text
reports/<repository-name>/<YYYYMMDD-HHMMSS>/
├── report.html              # HTML Report v2
├── report.json              # machine-readable assessment
├── findings.json            # deterministic rule findings
├── recommendations.json     # deterministic recommendations
├── ai-enrichment.json       # optional (--with-ai success)
├── ai-execution.json        # optional AI observability
└── graphs/
    ├── repository-manifest.json
    ├── repository-graph.json
    ├── engineering-knowledge-graph.json
    ├── knowledge-bindings.json
    ├── assessment-graph.json
    └── graph-summary.json
```

AIMF retains the latest **three** completed runs per repository.

---

## HTML report

HTML Report v2 is self-contained (embedded CSS, no external assets):

1. Executive Overview
2. Repository Profile
3. Technology and Version Summary
4. Assessment Summary
5. Findings (deterministic)
6. Recommendations (deterministic)
7. AI Enrichment (only when available; labeled AI-generated)
8. Graph and Artifact References
9. Assessment Metadata

Deterministic sections are authoritative. AI content is interpretive and kept
separate.

### Example screenshots

Placeholder paths for future screenshots (add PNGs under `docs/images/`):

| View | Placeholder |
| ---- | ----------- |
| Executive overview | `docs/images/report-executive-overview.png` |
| Findings | `docs/images/report-findings.png` |
| Recommendations | `docs/images/report-recommendations.png` |
| AI enrichment | `docs/images/report-ai-enrichment.png` |

Until screenshots land, generate a local report with the Quick Start commands and
open `report.html` in a browser.

---

## Supported technologies

| Area | Support in v0.1.0 |
| ---- | ----------------- |
| Languages | Java, JavaScript/TypeScript, PHP (detection + analyzers) |
| Build / deps | Maven (`pom.xml`), npm (`package.json`) |
| CI | GitHub Actions discovery |
| Static analysis | Optional PMD (Java) |
| AI | Amazon Bedrock Converse (optional) |
| Sources | Local filesystem, GitHub HTTPS/SSH |

---

## Roadmap

**Phase 2** — Core platform foundation (assessment, knowledge graphs, agents,
incremental assessment).

**Phase 3** — Enterprise Knowledge Graph (YAML workspace; optional; see
[docs/enterprise-knowledge-graph/](docs/enterprise-knowledge-graph/)).

**Phase 4.1** — Shared Rule Platform (infrastructure; see
[docs/analysis-intelligence/](docs/analysis-intelligence/)).

**Phase 4.1.2** — Assessment Framework methodology (see
[docs/assessment-framework/](docs/assessment-framework/)). Packs start at 4.2.

**Phase 4.2+ / 5+** — Analysis Intelligence packs, language expansion, workflow
intelligence, platform expansion. See [ROADMAP.md](ROADMAP.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy src
```

---

## Documentation index

| Doc | Topic |
| --- | ----- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design overview |
| [docs/runtime.md](docs/runtime.md) | Assess runtime pipeline |
| [docs/repository-graph.md](docs/repository-graph.md) | Inventory & repository graph |
| [docs/assessment-graph.md](docs/assessment-graph.md) | Assessment graph |
| [docs/rule-engine.md](docs/rule-engine.md) | Deterministic findings |
| [docs/recommendation-engine.md](docs/recommendation-engine.md) | Deterministic recommendations |
| [docs/ai-enrichment.md](docs/ai-enrichment.md) | One-call AI narrative |
| [docs/report-generation.md](docs/report-generation.md) | HTML Report v2 |
| [docs/knowledge-store.md](docs/knowledge-store.md) | Durable knowledge store + queries |
| [docs/mcp-server.md](docs/mcp-server.md) | CodeStrata FastMCP server |
| [docs/agent-framework.md](docs/agent-framework.md) | Agent Framework + `aimf agent` / MCP agent tools |
| [docs/enterprise-knowledge-graph/README.md](docs/enterprise-knowledge-graph/README.md) | Phase 3 Enterprise Knowledge Graph |
| [examples/README.md](examples/README.md) | Sample commands & expected outputs |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |

---

## License

MIT License — see [LICENSE](LICENSE).

## Author

Satish Nampally — https://github.com/sknampally
