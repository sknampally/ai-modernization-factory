# AI Modernization Factory

AI Modernization Factory (`aimf`) is a deterministic analysis platform for enterprise application modernization.

It clones a public GitHub repository, extracts structured facts about the codebase, detects technologies and engineering risks, and writes evidence-based reports. Use `aimf assess` for a customer-facing HTML report: deterministic by default (no cloud account required), or AI-enhanced with `--with-ai`.

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
* `aimf assess` with deterministic (default) and AI-enhanced HTML modernization reports
* Typed domain models, tests, Ruff, and MyPy

Not implemented yet:

* SonarQube / Semgrep / CodeQL providers
* Markdown modernization assessment reports

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
profile = "standard"  # focused | standard | comprehensive
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
PMD is the first supported Java provider and is recommended for deeper Java analysis.
PMD is optional: deterministic assessment succeeds without it.

* AIMF does not download or install PMD.
* When `fail_on_provider_error = false` and PMD is missing, assessment still
  succeeds and records PMD as `unavailable` in HTML, JSON, and console warnings.
* When `fail_on_provider_error = true`, an enabled but unavailable/failed
  provider fails the scan before reports are written.

#### PMD discovery order

1. `--pmd-path` on `aimf assess`
2. `AIMF_PMD_PATH` environment variable
3. `static_analysis.pmd.executable` from `aimf.toml` (command name or path)
4. `pmd` / `pmd-bin` on `PATH`
5. Common Homebrew locations on macOS (`/opt/homebrew/bin/pmd`, `/usr/local/bin/pmd`)

Validate a local install:

```bash
pmd --version
```

Optional environment override:

```bash
export AIMF_PMD_PATH=/path/to/pmd
```

Optional config:

```toml
[static_analysis.pmd]
enabled = true
executable = "pmd"  # or an absolute path to the executable
```

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

`aimf scan` reports are written under:

```text
reports/<repository-name>/<timestamp>/
├── report.txt
├── report.json
└── report.html
```

Only the latest 3 timestamped run directories are kept for each repository.

`aimf assess` writes immutable timestamped assessment runs:

```text
reports/
└── spring-petclinic/
    ├── 20260721-153045/
    │   ├── report.html
    │   └── report.json
    └── archive/
        └── 20260721-120000/
            ├── report.html
            └── report.json
```

* HTML is the customer-facing assessment
* JSON is the machine-readable assessment record for APIs, MCP, CI/CD, comparison, and knowledge-graph ingestion
* Each successful execution creates a new timestamped run directory
* Only the latest three active runs are kept under the repository directory; older runs are moved to `archive/`
* Both artifacts are produced from the same validated assessment input

### HTML report usability

The HTML report is self-contained (embedded CSS, no JavaScript) and is designed for desktop, mobile, and print:

* Long technical values wrap safely at path, package, coordinate, and URL delimiters
* Long repository-fact collections collapse behind native `<details>` controls (threshold: 8), with all values still present in the HTML and fully expanded in print
* Tables sit in local wrappers so any needed horizontal scrolling stays inside the component
* Evidence locations use repository-relative `path`, `path:line`, or `path:line:column` formatting consistently across HTML, console, and text reports
* Repository-derived and provider-derived text is HTML-escaped; absolute workspace, executable, and temporary provider paths are not shown
* PMD findings are normalized, grouped by rule/remediation pattern, and classified for customer visibility; raw observations remain in JSON
* Low-value or repetitive static-analysis observations may be summarized or omitted from HTML while remaining in `report.json`

## CLI

| Command | Description |
| ------- | ----------- |
| `aimf version` | Print the package version |
| `aimf scan` | Clone the configured GitHub repo, analyze it, write reports |
| `aimf assess` | Assess a local path or GitHub URL; write HTML and JSON assessment reports |

`scan` options:

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--config` / `-c` | `aimf.toml` | TOML configuration path |
| `--output` / `-o` | `text` | Terminal output format (`text` or `json`) |
| `--report-directory` | `reports` | Where report files are written |
| `--verbose` / `-v` | off | Print the full console report |

`assess` options (selected):

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--repo` / `-r` | required | Local repository path or GitHub URL |
| `--output` / `-o` | `reports` | Base directory for timestamped HTML and JSON assessment runs |
| `--with-ai` / `--no-ai` | `--no-ai` | Enable AI-enhanced assessment (requires credentials + model ID) |
| `--model-id` | none | Bedrock model ID (only with `--with-ai`) |
| `--pmd-path` | none | Optional PMD executable path/name (overrides env/config) |
| `--pmd-profile` | config (`standard`) | PMD profile: `focused`, `standard`, or `comprehensive` |
| `--static-analysis` / `--no-static-analysis` | follow config | Enable or disable external static analysis for this run |
| `--verbose` / `-v` | off | Diagnostic logging and failure stack traces |

### Assessment Execution Levels

AIMF supports three clearly separated assessment levels. Deterministic mode is the default and does **not** require AWS credentials, a Bedrock model ID, or any AI provider.

#### 1. Deterministic CLI Integration Test

Purpose: validate scanning, technology detection, deterministic analysis, serialization, HTML generation, file output, and CLI experience.

Requirements: no AWS, no model ID, no provider initialization, no prompt creation, no model invocation.

```bash
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports
```

#### 2. AI Integration Test

Purpose: validate prompt builder, provider integration, authentication, model response parsing, recommendation validation, and AI report sections.

Requirements: explicit `--with-ai`, a resolvable model ID (CLI → `AIMF_BEDROCK_MODEL_ID` → `ai.bedrock.model_id`), valid provider credentials, and exactly one model invocation.

```bash
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports \
  --with-ai \
  --model-id <model-id>
```

#### 3. Customer Acceptance Test

Purpose: run the complete product flow on a real repository and review the quality and usability of the generated report.

This uses the same AI-enhanced command as Level 2, treated as a manual acceptance workflow rather than only an integration check.

```bash
aimf assess \
  --repo <path-or-github-url> \
  --output reports \
  --with-ai \
  --model-id <model-id>
```

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
