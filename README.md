# AI Modernization Factory

AI Modernization Factory (`aimf`) is a deterministic analysis platform for enterprise application modernization.

It clones a public GitHub repository, extracts structured facts about the codebase, detects technologies and engineering risks, and writes evidence-based reports. AI interpretation of those structured findings is planned; the current product focuses on reliable, repeatable deterministic analysis first.

## Vision

Legacy enterprise applications are often difficult to understand, expensive to maintain, and risky to modernize. AIMF creates a repeatable assessment pipeline that:

1. Collects repository facts deterministically
2. Detects technologies and engineering issues
3. Produces evidence-backed findings
4. (Future) Uses small language models to interpret findings and generate modernization guidance

The goal is not to send an entire repository to a large language model for generic advice.

## Current Capabilities

Implemented today:

* Public GitHub repository cloning and local scanning
* Technology detection for Java, JavaScript/TypeScript, and PHP ecosystems
* Sequential analyzer pipeline with fact accumulation
* Build system discovery and metadata extraction
* Dependency discovery, metadata parsing, and health checks
* CI/CD pipeline discovery
* Console summary output plus text/JSON report files
* Typed domain models, tests, Ruff, and MyPy

Not implemented yet:

* Recommendation engine
* AI interpretation / executive summaries
* Security and quality rule packs beyond dependency health
* Markdown modernization assessment reports
* Local-path analyze command (scan currently uses `aimf.toml` GitHub URL)

## Quick Start

```bash
git clone https://github.com/sknampally/ai-modernization-factory.git
cd ai-modernization-factory

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

Configure the target repository in `aimf.toml`:

```toml
[repository]
url = "https://github.com/spring-projects/spring-petclinic"
branch = "main"

[workspace]
directory = ".aimf/workspace"
clean_before_clone = true
```

Run analysis:

```bash
aimf version
aimf scan
aimf scan --verbose
aimf scan --output json
aimf scan --report-directory reports
```

Reports are written under:

```text
reports/<repository-name>/<timestamp>/
├── report.txt
└── report.json
```

Only the latest 3 timestamped run directories are kept for each repository.
## CLI

| Command | Description |
| ------- | ----------- |
| `aimf version` | Print the package version |
| `aimf scan` | Clone the configured GitHub repo, analyze it, write reports |

`scan` options:

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--config` / `-c` | `aimf.toml` | TOML configuration path |
| `--output` / `-o` | `text` | Terminal output format (`text` or `json`) |
| `--report-directory` | `reports` | Where report files are written |
| `--verbose` / `-v` | off | Print the full console report |

## Analysis Pipeline

```text
aimf.toml
    │
    ▼
GitHubRepositoryScanner  ──►  Repository
    │
    ▼
CompositeTechnologyDetector
    │
    ▼
CompositeAnalyzer
    │
    ├─ RepositoryMetricsAnalyzer
    ├─ BuildDiscoveryAnalyzer
    ├─ BuildMetadataAnalyzer
    ├─ DependencyDiscoveryAnalyzer
    ├─ DependencyMetadataAnalyzer
    ├─ DependencyHealthAnalyzer
    └─ CicdDiscoveryAnalyzer
    │
    ▼
AnalysisResult (facts + findings)
    │
    ├─ report.txt
    ├─ report.json
    └─ console summary / JSON stdout
```

Each analyzer receives facts accumulated so far, returns new findings and newly produced facts, and `CompositeAnalyzer` merges those facts before calling the next analyzer.

## Project Structure

```text
ai-modernization-factory/
├── ARCHITECTURE.md
├── README.md
├── aimf.toml
├── pyproject.toml
├── src/aimf/
│   ├── cli.py
│   ├── config/
│   ├── models/
│   ├── reporters/
│   └── services/
│       ├── analysis_service.py
│       ├── analyzers/
│       ├── detectors/
│       └── scanners/
└── tests/
```

## Technology Stack

* Python 3.12
* Typer
* Pydantic
* Rich
* PyYAML
* pytest / Ruff / MyPy / setuptools

## Development

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

## Core Principles

* Deterministic analysis before AI reasoning
* Every finding must include evidence
* Analyzers are modular and replaceable
* The platform must remain useful without AI
* Prefer explicit, typed, tested code

## Roadmap

| Phase | Focus | Status |
| ----- | ----- | ------ |
| 1 | Repository intelligence, scanning, technology detection | Done |
| 2 | Deterministic analyzers (build, dependencies, CI/CD, metrics) | In progress |
| 3 | Recommendation engine | Planned |
| 4 | Richer reports and AI interpretation | Planned |
| 5 | Assisted refactoring and continuous modernization | Future |

See [ARCHITECTURE.md](ARCHITECTURE.md) for component details and design rationale.

## License

MIT License. See `LICENSE`.

## Author

Satish Nampally — https://github.com/sknampally
