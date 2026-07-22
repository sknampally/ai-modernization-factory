# AI Modernization Factory

AI Modernization Factory (`aimf`) is a deterministic analysis platform for enterprise application modernization.

It clones a public GitHub repository, extracts structured facts about the codebase, detects technologies and engineering risks, and writes evidence-based reports. Use `aimf assess` for a customer-facing HTML + JSON assessment: deterministic by default (no cloud account required), or AI-enhanced with `--with-ai`.

## Vision

Legacy enterprise applications are often difficult to understand, expensive to maintain, and risky to modernize. AIMF creates a repeatable assessment pipeline that:

1. Collects repository facts deterministically
2. Detects technologies and engineering issues
3. Produces evidence-backed findings and deterministic recommendations
4. Optionally runs AI reasoning over a budgeted, normalized evidence contract (not the raw repository)

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
* Architecture, security, and cloud-readiness analyzers
* Deterministic recommendation engine over findings
* Optional external static analysis (PMD for Java) with profiles, normalization, and grouping
* Baseline comparison between scans
* `aimf scan` — console summary plus text/JSON/HTML scan reports
* `aimf assess` — customer HTML + machine-readable JSON assessments (deterministic or AI-enhanced)
* AI assessment over normalized evidence (Amazon Bedrock), with validation and failure-safe deterministic reports
* Typed domain models, tests, Ruff, and MyPy

Not implemented yet:

* SonarQube / Semgrep / CodeQL providers
* Markdown modernization assessment reports
* Assisted refactoring / continuous modernization workflows

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

# Optional — AWS session + Bedrock Converse model for --with-ai
# (preferred over exporting AWS_PROFILE / AWS_REGION)
[aws]
profile = "aimf"
region = "us-east-1"

[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"
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

### AWS Setup (for `--with-ai`)

AIMF uses Amazon Bedrock's **Converse** API through a centralized AWS configuration module (`aimf.ai.aws_config`). After SSO login, you do **not** need to export `AWS_PROFILE` or `AWS_REGION`.

1. Install the AWS CLI v2.
2. Configure SSO once:

```bash
aws configure sso
```

Use a named profile such as `aimf` and choose the region where Bedrock is enabled (for example `us-east-1`).

3. Log in before AI-enhanced assessments:

```bash
aws sso login --profile aimf
```

4. Optional `aimf.toml` configuration (recommended):

```toml
[aws]
profile = "aimf"
region = "us-east-1"

[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"
```

If `ai.bedrock.model_id` is omitted, AIMF defaults to `amazon.nova-lite-v1:0`.

5. Run:

```bash
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports \
  --with-ai
```

Resolution order:

* Profile: `[aws].profile` → `AWS_PROFILE` → boto3 default credential chain
* Region: `[aws].region` → legacy `[ai.bedrock].region` → `AWS_REGION` / `AWS_DEFAULT_REGION` → boto3 default
* Model ID: `--model-id` → `AIMF_BEDROCK_MODEL_ID` → `[ai.bedrock].model_id` → `amazon.nova-lite-v1:0`

The Bedrock provider is model-family neutral (Converse API). It does not use Anthropic-specific `invoke_model` payloads.

If authentication fails, AIMF prints guidance such as `aws sso login --profile <profile>` without exposing boto3 stack traces. Deterministic HTML/JSON reports are still written.

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

#### PMD profiles

| Profile | Default | Intent |
| ------- | ------- | ------ |
| `focused` | no | Correctness, security, and significant design risks; lower stylistic noise |
| `standard` | **yes** | Normal modernization assessment (error-prone, design, selected best practices) |
| `comprehensive` | no | Broader evidence including lower-priority convention/style findings |

Override per run with `--pmd-profile`, or set `static_analysis.pmd.profile` in `aimf.toml`.

#### Normalization and customer visibility

* Raw PMD observations remain in `report.json`
* Customer HTML uses **normalized, grouped, prioritized** findings (not one card per raw observation)
* Visibility classes: `primary`, `supporting`, `informational`, `suppressed_from_html`
* Critical/high findings are never suppressed from customer HTML

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

## CLI

| Command | Description |
| ------- | ----------- |
| `aimf version` | Print the package version |
| `aimf scan` | Clone the configured GitHub repo, analyze it, write scan reports |
| `aimf assess` | Assess a local path or GitHub URL; write HTML and JSON assessment reports |

### `aimf scan`

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

Only the latest 3 timestamped run directories are kept for each repository (older runs are deleted).

`scan` options:

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--config` / `-c` | `aimf.toml` | TOML configuration path |
| `--output` / `-o` | `text` | Terminal output format (`text` or `json`) |
| `--report-directory` | `reports` | Where report files are written |
| `--verbose` / `-v` | off | Print the full console report |

### `aimf assess`

`aimf assess` writes immutable timestamped assessment runs with **HTML + JSON only** (no `report.txt`):

```text
reports/
└── spring-petclinic/
    ├── 20260721-153045/
    │   ├── report.html
    │   ├── report.json
    │   └── ai-execution.json   # only when an AI provider was invoked
    ├── 20260721-160000/
    │   ├── report.html
    │   └── report.json
    └── 20260721-170000/
        ├── report.html
        ├── report.json
        └── ai-execution.json
```

* `report.html` is the customer-readable assessment
* `report.json` is the machine-readable assessment record (schema/report version **1.2**) for APIs, MCP, CI/CD, comparison, and knowledge-graph ingestion
* `ai-execution.json` is an internal AI observability / evaluation artifact created only when an AI provider is invoked (success or failure). It is not a customer deliverable, is never linked from HTML, and should be treated as potentially sensitive repository-derived data. It is future-compatible evaluation data for model comparison, prompt evaluation, regression analysis, and benchmarking — not a fine-tuning pipeline
* Each successful execution creates a new timestamped run directory
* MVP retention keeps only the latest **three completed** runs per repository; older completed runs are deleted automatically (including any `ai-execution.json` in that run)
* Completed-run detection depends only on `report.html` and `report.json`
* No local `archive/` directory is created
* Retention runs only after successful artifact generation
* Longer retention / cloud archival is deferred and is expected to use customer-owned storage when required later — not local AIMF archive folders
* Customer HTML and JSON are produced from the same validated assessment input

```bash
# Deterministic (default) — no AWS required
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports \
  --pmd-profile standard

# AI-enhanced — one Bedrock invocation over normalized evidence
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports \
  --with-ai
```

Model ID and AWS profile/region can come from `aimf.toml` (see AWS Setup). Override the model when needed:

```bash
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports \
  --with-ai \
  --model-id <bedrock-model-id>
```

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

Model ID resolution for `--with-ai`: CLI `--model-id` → `AIMF_BEDROCK_MODEL_ID` → `ai.bedrock.model_id` → default `amazon.nova-lite-v1:0`.

AWS profile/region resolution: `[aws]` in `aimf.toml` → environment variables → boto3 default chain. No manual `export AWS_PROFILE` / `export AWS_REGION` is required when `[aws]` is configured.

### Assessment execution levels

AIMF supports three clearly separated assessment levels. Deterministic mode is the default and does **not** require AWS credentials, a Bedrock model ID, or any AI provider.

#### 1. Deterministic CLI integration test

Purpose: validate scanning, technology detection, deterministic analysis, serialization, HTML generation, file output, and CLI experience.

```bash
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports
```

#### 2. AI integration test

Purpose: validate prompt builder, provider integration, authentication, model response parsing, recommendation validation, and AI report sections.

Requirements: explicit `--with-ai`, a resolvable model ID, valid provider credentials, and exactly one model invocation.

```bash
aimf assess \
  --repo .aimf/workspace/spring-petclinic \
  --output reports \
  --with-ai \
  --model-id <model-id>
```

#### 3. Customer acceptance test

Purpose: run the complete product flow on a real repository and review report quality.

```bash
aimf assess \
  --repo <path-or-github-url> \
  --output reports \
  --with-ai \
  --model-id <model-id>
```

### AI-enhanced assessment

When `--with-ai` is set:

1. Deterministic analysis and PMD run first (PMD at most once)
2. AIMF builds a budgeted `LLMAnalysisContext` from **normalized** intelligence (not all raw PMD observations)
3. Exactly one Bedrock model call produces a typed `AIRecommendationResult`
4. Evidence validation rejects unknown finding/group IDs, empty material evidence, unsupported severity escalation, and invented paths
5. HTML and JSON are written from the same report input; AI content is appended to the same report (not a separate artifact)

AIMF distinguishes three customer-facing outcomes:

| Outcome | When | Report content |
| --- | --- | --- |
| Deterministic assessment | `--no-ai` (default) | Deterministic evidence only; AI marked `not_requested` |
| Successful AI-enhanced assessment | Provider call succeeds and the response passes contract validation | Deterministic evidence plus validated AI interpretation |
| Deterministic fallback after AI failure | AI was requested but auth, provider, parsing, or validation failed | Deterministic evidence only; AI status records the failure stage |

If AI provider execution, parsing, or validation fails:

* Deterministic HTML and JSON are still written
* AI status is recorded with an explicit lifecycle value (`authentication_failed`, `provider_failed`, `parsing_failed`, or `validation_failed`) — not as “AI not executed”
* Provider/model/token/latency metadata is retained when the provider call succeeded before the failure
* An internal `ai-execution.json` is written beside the run reports whenever AI was requested (success or failure), capturing raw/parsed/accepted layers when available, normalization metadata, and failure stage/code. It is not a customer deliverable and is never linked from the HTML report. `report.json` may name the artifact via `internal_execution_artifact` without embedding its contents
* Unvalidated AI recommendations are never included in the customer-facing report
* Customer-facing warnings stay concise (for example `AI_VALIDATION_FAILED`); detailed validation errors stay in JSON metadata, the execution artifact, and debug logs
* Raw model responses and prompts are never exposed in HTML
* No fabricated AI sections are inserted

AI input includes repository identity, technology inventory, architecture/build/dependency/CI/CD/security/cloud facts, static-analysis profile summary, AIMF-native findings, grouped PMD findings, deterministic recommendations, and coverage warnings.

AI output (when successful) includes executive interpretation, key modernization risks (≤5), consolidated AI recommendations (5–8 outcome-oriented initiatives with response-local IDs `AI-REC-001`…), modernization phases (2–4), limitations, evidence coverage recalculated by AIMF from unique `related_finding_ids`, and token/latency metadata.

AI recommendations must synthesize deterministic findings and deterministic recommendations into broader modernization initiatives. They must not copy each deterministic remediation item one-for-one. Traceability uses `related_finding_ids` and optional `related_deterministic_recommendation_ids`.

### HTML report usability

The HTML report is self-contained (embedded CSS, no JavaScript) and is designed for desktop, mobile, and print:

* Long technical values wrap safely at path, package, coordinate, and URL delimiters
* Long repository-fact collections collapse behind native `<details>` controls (threshold: 8), with all values still present in the HTML and fully expanded in print
* Tables sit in local wrappers so any needed horizontal scrolling stays inside the component
* Evidence locations use repository-relative `path`, `path:line`, or `path:line:column` formatting
* Repository-derived and provider-derived text is HTML-escaped; absolute workspace, executable, and temporary provider paths are not shown
* PMD findings are normalized, grouped by rule/remediation pattern, and classified for customer visibility; raw observations remain in JSON
* Deterministic recommendations appear first (grouped by category for readability); AI recommendations appear later and are clearly labeled
* AI evidence references link to deterministic finding/group anchors

### Spring Petclinic reference (standard PMD profile)

Approximate validated counts for the bundled Spring Petclinic workspace:

| Signal | Approx. count |
| ------ | ------------- |
| Java files analyzed by PMD | 49 |
| Raw PMD observations | ~159 |
| Grouped PMD findings | ~27 |
| Total customer findings | ~34 |
| HTML finding cards | ~25 |
| Deterministic recommendations | ~12 |

## Analysis Pipeline

```text
aimf.toml / CLI
    │
    ▼
Repository scanner (local or GitHub)
    │
    ▼
AnalysisService
    ├─ Technology detection
    ├─ CompositeAnalyzer (metrics → build → deps → CI/CD → security → architecture → cloud)
    ├─ StaticAnalysisService (PMD profiles → normalize → group → visibility)
    └─ Deterministic recommendation engine
    │
    ▼
AnalysisResult
    │
    ├─ aimf scan  → report.txt + report.json + report.html
    └─ aimf assess
           ├─ (optional) budgeted AI context → one Bedrock call → validated AI result
           └─ report.html + report.json (+ ai-execution.json when AI invoked; keep latest 3 completed runs)
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
│   ├── cli/                 # version, scan, assess
│   ├── config/
│   ├── models/
│   ├── reporters/           # scan-oriented text/JSON/HTML reporters
│   ├── reporting/           # assess HTML/JSON modernization reports
│   ├── ai/                  # contracts, prompts, providers, agents, validation
│   ├── static_analysis/     # PMD provider, profiles, normalization, grouping
│   ├── repository_auth/
│   ├── security/
│   └── services/
│       ├── analysis_service.py
│       ├── recommendation_engine.py
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
* Amazon Bedrock (optional, `--with-ai` only)
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
* AI augments the same report; it does not replace deterministic evidence
* Prefer explicit, typed, tested code

## Roadmap

| Phase | Focus | Status |
| ----- | ----- | ------ |
| 1 | Repository intelligence, scanning, technology detection | Done |
| 2 | Deterministic analyzers (build, dependencies, CI/CD, security, architecture, cloud) | Done |
| 3 | Deterministic recommendation engine | Done |
| 4 | PMD static analysis with profiles, normalization, and grouping | Done |
| 5 | Customer assess reports (HTML + JSON) with latest-3 retention | Done |
| 6 | AI interpretation over normalized evidence (Bedrock) | Done (first release) |
| 7 | Additional static-analysis providers (SonarQube / Semgrep / CodeQL) | Planned |
| 8 | Assisted refactoring and continuous modernization | Future |

See [ARCHITECTURE.md](ARCHITECTURE.md) for component details and design rationale.

## License

MIT License. See `LICENSE`.

## Author

Satish Nampally — https://github.com/sknampally
