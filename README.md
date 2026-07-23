# AI Modernization Factory

AI Modernization Factory (`aimf`) analyzes application repositories, detects technologies and engineering risks, and writes evidence-based HTML and JSON assessment reports.

Deterministic analysis works without cloud credentials. Optional AI-enhanced assessment uses Amazon Bedrock when you pass `--with-ai`.

## Clone

```bash
git clone https://github.com/sknampally/ai-modernization-factory.git
cd ai-modernization-factory
```

Cloning the repository does **not** install the Python package. Continue with the virtual environment and install steps below.

## Virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Installation

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For contribution / running the full test suite:

```bash
python -m pip install -e ".[dev]"
```

## Installation verification

```bash
python -c "import aimf; print(aimf.__file__)"
aimf version
aimf --help
aimf assess --help
```

If `import aimf` fails, the editable install is missing or the virtual environment is not active.

## Configuration

### `aimf.toml`

Primary configuration file (loaded with `--config aimf.toml`).

Repository selection for `aimf assess`:

1. `--repo` on the command line (highest priority)
2. `[repository].path` in `aimf.toml` (local checkout)
3. `[repository].url` in `aimf.toml` (GitHub HTTPS or SSH URL)
4. otherwise AIMF fails with an actionable error (never falls back to a demo repository)

The shipped `aimf.toml` points at the bundled sample app:

```toml
[repository]
path = "examples/sample-js-app"
```

Point AIMF at **your** repository:

```toml
[repository]
path = "/absolute/or/relative/path/to/your-repo"
```

Or clone from GitHub (also required for `aimf scan`):

```toml
[repository]
url = "https://github.com/YOUR_ORG/YOUR_REPO"
branch = "main"
```

Supported `[repository]` fields: `path`, `url`, `branch`, and optional `authentication` (`github_token` with `token_env`, or `ssh_agent`).

### `.env`

AIMF automatically loads a `.env` file when reading configuration (walking upward from the config directory and the current working directory). Existing shell environment variables are never overwritten.

```bash
cp .env.example .env
```

Common variables (names only; do not commit secrets):

| Variable | Purpose |
| -------- | ------- |
| `AIMF_GITHUB_TOKEN` | Private GitHub HTTPS clone token (referenced by name from `aimf.toml`) |
| `AIMF_BEDROCK_MODEL_ID` | Optional Bedrock model override for `--with-ai` |
| `AWS_PROFILE` / `AWS_REGION` | Optional AWS overrides (prefer `[aws]` in `aimf.toml`) |
| `AIMF_LOG_LEVEL` | Logging level (`WARNING` default) |

You do **not** need to run `source .env`.

### AWS credentials (optional, for `--with-ai`)

Configure a named profile with the AWS CLI, then authenticate:

```bash
aws sso login --profile <profile-name>
AWS_PROFILE=<profile-name> aws sts get-caller-identity
```

Point AIMF at that profile via `aimf.toml` (preferred):

```toml
[aws]
profile = "<profile-name>"
region = "us-east-1"

[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"
```

Or export `AWS_PROFILE` / `AWS_REGION` in the environment. AIMF uses the configured profile for Bedrock when you pass `--with-ai`.

### GitHub token (optional, private repos)

```bash
# in .env (never commit secrets)
AIMF_GITHUB_TOKEN=your-token-value
```

```toml
[repository]
url = "https://github.com/your-org/private-repo"
branch = "main"

[repository.authentication]
type = "github_token"
token_env = "AIMF_GITHUB_TOKEN"
```

Never put token values in `aimf.toml`.

## Assessment

Canonical workflow:

```bash
aimf assess --config aimf.toml --output reports --with-ai
```

Deterministic only (no AWS / Bedrock required):

```bash
aimf assess --config aimf.toml --output reports
```

Override the configured repository for one run:

```bash
aimf assess --repo /path/to/your-repo --config aimf.toml --output reports
```

### `aimf scan` (clone + scan reports)

`aimf scan` clones the GitHub URL from `[repository].url` and writes text/JSON/HTML scan reports. It requires `url` (local `path` alone is not enough):

```bash
aimf scan --config aimf.toml --report-directory reports
```

## Output

Assessment reports are written under timestamped run directories:

```text
reports/<repository-name>/<YYYYMMDD-HHMMSS>/
├── report.html          # customer-facing assessment
├── report.json          # machine-readable assessment
├── findings.json        # deterministic Assessment Graph rule findings
├── recommendations.json # deterministic finding → modernization recommendations
├── ai-enrichment.json   # optional AI narrative (--with-ai only, on success)
├── ai-execution.json    # only for --with-ai attempts (internal)
└── graphs/              # deterministic Phase 2 graph artifacts
    ├── repository-manifest.json
    ├── repository-graph.json
    ├── engineering-knowledge-graph.json
    ├── knowledge-bindings.json
    ├── assessment-graph.json
    └── graph-summary.json
```

AIMF keeps the latest three completed runs per repository.

**Deterministic analysis** (`--no-ai`, the default) scans the repository, runs
analyzers, builds knowledge-graph artifacts, evaluates Assessment Graph rules,
derives deterministic recommendations from those findings, and writes
evidence-based HTML/JSON without calling a cloud model.

**`--with-ai`** adds one Bedrock enrichment call over compact context built from
deterministic findings, recommendations, and a repository/technology summary.
It writes `ai-enrichment.json` on success. Full graph JSON is not sent to the
model. Deterministic `findings.json` / `recommendations.json` are never modified
by AI. If AI fails, deterministic reports and graphs are kept and the CLI
completes with a warning (non-zero exit is not used for AI enrichment failure).

### Deterministic findings and recommendations

```text
Repository Graph → Assessment Graph → Rules → Findings → Recommendations
→ optional AI enrichment / reporting
```

| Layer | Artifact | Role |
| ----- | -------- | ---- |
| Rules | `findings.json` | Deterministic Assessment Graph findings |
| Recommendations | `recommendations.json` | Actionable steps derived only from findings |
| AI enrichment | `ai-enrichment.json` | Concise narrative over findings + recommendations |

AI enrichment is interpretive only. Traceability uses referenced finding and
recommendation IDs from the compact context allowlists. Exactly one provider
call runs in `--with-ai` mode; deterministic mode makes zero provider calls.

### Graph artifacts (brief)

| Artifact | Meaning |
| -------- | ------- |
| Repository Graph | Structural view of the assessed repository (files, modules, dependencies, …) |
| Engineering Knowledge Graph | Reusable engineering concepts from the builtin catalog |
| Knowledge Bindings | Deterministic links from repository observations to concepts |
| Assessment Graph | Assessment-scoped projection of those accepted bindings |

These artifacts feed the Rule Engine and Recommendation Engine. They are also
machine-readable context for future AI-assisted narrative (not yet wired to
consume recommendation JSON).

## Troubleshooting

### `ModuleNotFoundError: No module named 'aimf'`

The package is not installed in the active environment (cloning alone is not enough).

```bash
source .venv/bin/activate
python -m pip install -e .
python -c "import aimf; print(aimf.__file__)"
aimf version
```

### AWS SSO / Bedrock authentication failed

```bash
aws sso login --profile <profile-name>
AWS_PROFILE=<profile-name> aws sts get-caller-identity
aimf assess --config aimf.toml --output reports --with-ai
```

Confirm `[aws].profile` / `[aws].region` and Bedrock model access in that account/region. Deterministic HTML/JSON are still written if AI fails.

### GitHub authentication failed

- HTTPS: ensure `AIMF_GITHUB_TOKEN` is set (via `.env` or the shell) and `token_env` matches that name
- SSH: ensure your agent has a loaded key (`ssh-add -l`) and the URL uses `git@github.com:...`
- Confirm the token/SSH key can read the repository

### Repository not found / path does not exist

```bash
# Local path
ls examples/sample-js-app
aimf assess --repo examples/sample-js-app --output reports

# Or update aimf.toml [repository].path / .url
```

### Missing configuration

```text
No repository configured.
```

Set `[repository].path` or `[repository].url` in `aimf.toml`, or pass `--repo`.

```text
Configuration file does not exist: aimf.toml
```

Run from the project root, or pass `--config /path/to/aimf.toml`.

### `aimf scan` says URL is required

`scan` only clones GitHub URLs. Set `[repository].url`, or use `aimf assess --repo <local-path>` for local checkouts.

## CLI reference

| Command | Purpose |
| ------- | ------- |
| `aimf version` | Print package version |
| `aimf assess` | Primary assessment workflow (HTML + JSON) |
| `aimf scan` | Clone configured GitHub repo; write scan reports |

Useful `assess` flags:

| Flag | Description |
| ---- | ----------- |
| `--config` / `-c` | TOML config path (default `aimf.toml`) |
| `--repo` / `-r` | Local path or GitHub URL (overrides config) |
| `--output` / `-o` | Report base directory (default `reports`) |
| `--with-ai` / `--no-ai` | AI-enhanced vs deterministic (default `--no-ai`) |
| `--model-id` | Bedrock model override (requires `--with-ai`) |
| `--verbose` / `-v` | Diagnostic logging |

## Optional sample app

The repository includes `examples/sample-js-app`, a tiny Node.js sample used for onboarding and tests. It is **not** required for production use. Replace `[repository].path` with your own application as soon as you are ready.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy src
```

## Capabilities (summary)

* Local path and public/private GitHub repository assessment
* Technology detection for Java, JavaScript/TypeScript, and PHP ecosystems
* Build, dependency, CI/CD, architecture, security, and cloud-readiness analyzers
* Deterministic recommendations with evidence
* Optional PMD static analysis for Java
* Optional Bedrock AI interpretation over normalized evidence

See [ARCHITECTURE.md](ARCHITECTURE.md), [docs/architecture/assessment-graph.md](docs/architecture/assessment-graph.md), and [docs/architecture/assess-runtime-graphs.md](docs/architecture/assess-runtime-graphs.md) for component details.

## License

MIT License. See `LICENSE`.

## Author

Satish Nampally — https://github.com/sknampally
