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
* Private GitHub HTTPS cloning via environment-variable token references
* Private GitHub SSH cloning via the user's existing SSH agent
* Technology detection for Java, JavaScript/TypeScript, and PHP ecosystems
* Sequential analyzer pipeline with fact accumulation
* Build system discovery and metadata extraction
* Dependency discovery, metadata parsing, and health checks
* CI/CD pipeline discovery
* Architecture and cloud-readiness signals
* Optional external static-analysis providers (PMD for Java)
* Baseline comparison between scans
* Console summary plus text/JSON/HTML report files
* Typed domain models, tests, Ruff, and MyPy

Not implemented yet:

* AI interpretation / executive summaries
* SonarQube / Semgrep / CodeQL providers
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

[static_analysis]
enabled = true
fail_on_provider_error = false

[static_analysis.pmd]
enabled = true
executable = "pmd"
rulesets = [
  "category/java/bestpractices.xml",
  "category/java/errorprone.xml",
  "category/java/design.xml",
]
minimum_priority = 5
timeout_seconds = 120
```

### Private GitHub repositories

AIMF can clone private GitHub repositories without storing credentials in `aimf.toml`, URLs, reports, or Git configuration.

#### HTTPS token (recommended for CI and local HTTPS remotes)

1. Create a fine-grained GitHub token with least privilege (read-only Contents/Metadata for required repositories).
2. Export the token in your shell environment (never commit it):

```bash
export AIMF_GITHUB_TOKEN="your-token-value"
```

3. Reference the environment variable name only:

```toml
[repository]
url = "https://github.com/your-org/private-repo"
branch = "main"

[repository.authentication]
type = "github_token"
token_env = "AIMF_GITHUB_TOKEN"
```

4. Scan:

```bash
aimf scan --config aimf.toml
```

Never place `token`, `password`, `secret`, or private-key material in `aimf.toml`.

#### SSH agent

```toml
[repository]
url = "git@github.com:your-org/private-repo.git"

[repository.authentication]
type = "ssh_agent"
```

AIMF relies on your existing SSH agent, SSH config, and `known_hosts` behavior. It does not copy keys, disable host-key checking, or modify `known_hosts`.

SSH URLs without an authentication section continue to use normal Git/SSH agent behavior.

#### Common sanitized errors

| Situation | Message |
| --------- | ------- |
| Missing/blank token env var | The configured credential environment variable is not available. |
| Bad credentials | GitHub authentication failed. Verify the configured credential. |
| Ambiguous private/missing repo | The repository could not be accessed. Verify the repository URL and credential permissions. |
| HTTPS URL with `ssh_agent` | Configuration error (incompatible authentication type). |
| SSH URL with `github_token` | Configuration error (incompatible authentication type). |

#### Current local-CLI limitations

* GitHub only (no GitLab/Bitbucket/Azure DevOps)
* No GitHub App, OAuth browser, or AWS Secrets Manager integration
* No token persistence or PAT creation helpers
* Authentication applies to remote clones only; local path scanning ignores it

### External static analysis (PMD)

AIMF can optionally run external engines through a provider architecture.
PMD is the first supported Java provider.

* PMD must be installed and available on `PATH` (or configured via `executable`).
* AIMF does not download or install PMD.
* When `fail_on_provider_error = false` and PMD is missing, the scan still
  succeeds and reports PMD as `unavailable`.
* When `fail_on_provider_error = true`, an enabled but unavailable/failed
  provider fails the scan before reports are written.

Example:

```bash
aimf scan --config aimf.toml
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
├── report.json
└── report.html
```

Only the latest 3 timestamped run directories are kept for each repository.

### HTML report usability

The HTML report is self-contained (embedded CSS, no JavaScript) and is designed for desktop, mobile, and print:

* Long technical values wrap safely at path, package, coordinate, and URL delimiters
* Long repository-fact collections collapse behind native `<details>` controls (threshold: 8), with all values still present in the HTML and fully expanded in print
* Tables sit in local wrappers so any needed horizontal scrolling stays inside the component
* Evidence locations use repository-relative `path`, `path:line`, or `path:line:column` formatting consistently across HTML, console, and text reports
* Repository-derived and provider-derived text is HTML-escaped; absolute workspace, executable, and temporary provider paths are not shown

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
