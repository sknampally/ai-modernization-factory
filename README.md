# AI Modernization Factory

AI Modernization Factory is an AI-assisted platform that analyzes enterprise applications, identifies engineering risks, and generates actionable modernization recommendations.

The platform combines deterministic repository analysis, engineering rules, and lightweight AI models to produce evidence-based modernization assessments.

The goal is not to send an entire repository to a large language model and ask for generic advice. Instead, the platform first extracts structured facts, detects issues through deterministic analysis, and then uses a small language model to interpret findings, prioritize recommendations, and generate a clear modernization report.

## Vision

Legacy enterprise applications are often difficult to understand, expensive to maintain, and risky to modernize.

Teams frequently lack:

* Accurate documentation
* Clear architecture visibility
* A prioritized view of technical debt
* Reliable modernization recommendations
* Cost-effective ways to analyze large applications
* A practical roadmap for modernization

AI Modernization Factory aims to address this problem by creating a repeatable application assessment pipeline.

The platform analyzes an application repository, identifies evidence-based engineering risks, prioritizes findings, and generates an actionable modernization assessment.

Over time, the platform can evolve from assessment into assisted transformation, including refactoring recommendations, code generation, validation, and continuous modernization monitoring.

## What the Platform Does

The AI Modernization Factory processes an application through several stages:

```text
Application Repository
        |
        v
Repository Intelligence
        |
        v
Deterministic Issue Detection
        |
        v
AI-Assisted Interpretation
        |
        v
Prioritized Recommendations
        |
        v
Modernization Assessment Report
```

The initial MVP will support the following capabilities:

1. Repository intelligence
2. Technology and dependency detection
3. Engineering issue detection
4. Security and quality checks
5. Recommendation generation
6. Finding prioritization
7. Markdown and JSON reports
8. AI-assisted executive summaries
9. Small-model-based recommendation enrichment

## Core Principles

### Deterministic Analysis Before AI Reasoning

The system should first gather reliable facts using deterministic analysis.

Examples include:

* File structure
* Programming languages
* Frameworks
* Dependencies
* Configuration files
* Test presence
* Potential hardcoded secrets
* Large files
* Debug statements
* Empty exception handlers
* Missing documentation

AI should interpret structured evidence rather than invent facts directly from an unstructured repository.

### Use the Smallest Model That Meets the Quality Requirement

The MVP will use small language models for tasks such as:

* Summarizing findings
* Grouping related issues
* Explaining why findings matter
* Generating recommendations
* Producing executive summaries
* Suggesting modernization priorities

The platform should avoid unnecessary dependency on expensive frontier models.

### Every Recommendation Must Be Backed by Evidence

Each finding should include:

* Title
* Category
* Severity
* Confidence
* Evidence
* File location
* Explanation
* Recommendation
* Estimated effort
* Suggested priority

A recommendation without supporting evidence should not be treated as a reliable engineering finding.

### AI Assists Engineers

The platform should support engineering judgment, not replace it.

AI-generated recommendations should be:

* Reviewable
* Traceable
* Configurable
* Supported by evidence
* Clearly distinguished from deterministic findings

### Modular and Replaceable Components

Repository scanners, analyzers, reporting engines, and model providers should be modular.

The platform should support different:

* Programming languages
* Application frameworks
* Rule engines
* Model providers
* Report formats
* Deployment environments

## Example Finding

```text
Issue:
Possible hardcoded database credential

Category:
Security

Severity:
Critical

Confidence:
High

Evidence:
src/config/database.py:18

Why It Matters:
Hardcoded credentials may be exposed through source control,
logs, shared environments, or unauthorized repository access.

Recommendation:
Move the credential into an environment variable and use a
managed secret store in deployed environments.

Estimated Effort:
Small

Suggested Priority:
Immediate
```

## MVP Scope

The first meaningful version of the platform will provide an end-to-end application assessment.

### Repository Intelligence

The platform will collect:

* Repository name and location
* File and directory counts
* Programming languages
* Framework indicators
* Dependency files
* Dependency versions
* Configuration files
* Application entry points
* Test files
* Database indicators
* Infrastructure indicators
* Code and file statistics

### Issue Detection

The MVP will include focused deterministic checks such as:

* Possible hardcoded credentials
* Missing environment configuration
* Debug statements
* Empty exception handlers
* Large files
* Missing tests
* Missing project documentation
* Potential insecure configuration
* Outdated dependency indicators
* Unpinned dependencies
* Generated files committed to source control
* Suspicious configuration patterns

The initial goal is to provide a small number of high-value rules rather than a large number of shallow checks.

### Recommendation Engine

The recommendation engine will:

* Convert findings into actionable recommendations
* Group related issues
* Assign severity and priority
* Estimate remediation effort
* Identify quick wins
* Separate immediate risks from long-term modernization needs

### Modernization Report

The MVP will generate:

```text
output/
├── analysis.json
├── findings.json
└── modernization-report.md
```

The Markdown report will include:

1. Executive summary
2. Application profile
3. Technology overview
4. Key risks
5. Prioritized findings
6. Recommended modernization initiatives
7. Quick wins
8. Longer-term roadmap
9. Confidence and limitations
10. Model usage and cost information

## Example CLI Usage

```bash
ai-factory analyze ./sample-app
```

Additional options may include:

```bash
ai-factory analyze ./sample-app --output ./output
ai-factory analyze ./sample-app --format markdown
ai-factory analyze ./sample-app --no-ai
ai-factory analyze ./sample-app --model small
```

The platform should remain useful when AI is disabled.

The `--no-ai` mode will generate deterministic findings and reports without calling a language model.

## Architecture

The planned package structure is:

```text
src/amf/
├── cli.py
├── models/
│   ├── repository.py
│   ├── finding.py
│   ├── recommendation.py
│   └── report.py
├── intelligence/
│   ├── scanner.py
│   ├── language_detector.py
│   ├── dependency_detector.py
│   └── framework_detector.py
├── analyzers/
│   ├── base.py
│   ├── security.py
│   ├── quality.py
│   ├── testing.py
│   └── dependencies.py
├── recommendations/
│   ├── engine.py
│   └── prioritizer.py
├── ai/
│   ├── provider.py
│   ├── analyst.py
│   └── prompts.py
├── reporting/
│   ├── markdown.py
│   └── json_reporter.py
└── orchestration/
    └── pipeline.py
```

The implementation will be incremental. This structure represents the intended product architecture, not a requirement to create every module immediately.

## AI Strategy

The AI layer will operate on structured findings rather than raw repositories whenever possible.

```text
Repository
    |
    v
Deterministic Analysis
    |
    v
Structured Findings
    |
    v
Small Language Model
    |
    v
Recommendations and Report Narrative
```

The model layer should support:

* Pluggable model providers
* Structured JSON output
* Schema validation
* Retry and failure handling
* Token usage tracking
* Latency tracking
* Estimated cost tracking
* AI-disabled operation
* Confidence indicators

A conceptual model provider interface may look like:

```python
from typing import Protocol


class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...
```

Model configuration may be provided through environment variables:

```env
AMF_AI_ENABLED=true
AMF_MODEL_PROVIDER=openai
AMF_MODEL_NAME=small-model
AMF_OUTPUT_DIR=output
AMF_LOG_LEVEL=INFO
```

The platform may later support local models through tools such as Ollama.

## Technology Stack

The initial implementation uses:

* Python 3.12
* Typer
* Pydantic
* Rich
* pytest
* Ruff
* MyPy
* setuptools

Additional libraries will be introduced only when there is a clear need.

## Roadmap

### Phase 1: Repository Intelligence

* Scan repository structure
* Detect languages
* Detect frameworks
* Detect dependency files
* Identify tests and configuration
* Produce structured repository metadata

### Phase 2: Issue Detection Engine

* Create a common analyzer interface
* Add security checks
* Add quality checks
* Add testing checks
* Add dependency checks
* Generate structured findings

### Phase 3: Recommendation Engine

* Prioritize findings
* Estimate effort
* Group related issues
* Identify quick wins
* Generate remediation guidance

### Phase 4: Modernization Assessment Reports

* Generate Markdown reports
* Generate JSON reports
* Add executive summaries
* Add risk and priority summaries
* Track model usage and cost

### Phase 5: AI-Assisted Refactoring

* Suggest code changes
* Generate refactoring plans
* Produce change previews
* Validate generated changes
* Support human approval workflows

### Phase 6: Continuous Modernization Platform

* Monitor repositories continuously
* Detect regressions
* Track modernization progress
* Compare assessment history
* Integrate with pull requests and CI/CD
* Recommend the lowest-cost model that meets quality requirements

## Capability Roadmap

| Capability                     | MVP | Future |
| ------------------------------ | --: | -----: |
| Repository intelligence        | Yes |        |
| Language detection             | Yes |        |
| Framework detection            | Yes |        |
| Dependency detection           | Yes |        |
| Issue detection                | Yes |        |
| Security checks                | Yes |        |
| Quality checks                 | Yes |        |
| Recommendations                | Yes |        |
| Markdown report                | Yes |        |
| JSON report                    | Yes |        |
| AI executive summary           | Yes |        |
| Small-model support            | Yes |        |
| AI-disabled mode               | Yes |        |
| Cost and token tracking        | Yes |        |
| Pull request generation        |     |    Yes |
| Automated code refactoring     |     |    Yes |
| Architecture diagrams          |     |    Yes |
| Continuous monitoring          |     |    Yes |
| Regression detection           |     |    Yes |
| Model quality evaluation       |     |    Yes |
| Model routing and optimization |     |    Yes |

## Engineering Philosophy

This project follows several engineering practices:

* Build incrementally
* Keep components small and focused
* Use strong typing
* Validate external inputs
* Write tests with every feature
* Prefer explicit code over unnecessary abstraction
* Document architectural decisions
* Keep deterministic and AI-generated outputs distinguishable
* Avoid premature framework adoption
* Track limitations honestly
* Design for model replacement
* Keep the platform useful without AI

## Project Structure

```text
ai-modernization-factory/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── coding-standards.md
│   ├── contribution.md
│   └── decisions/
│       └── 0001-initial-architecture.md
├── output/
│   └── .gitkeep
├── src/
│   └── amf/
│       ├── __init__.py
│       └── cli.py
├── tests/
│   └── test_cli.py
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

The structure will evolve as the application capabilities are implemented.

## Development Setup

Clone the repository:

```bash
git clone https://github.com/sknampally/ai-modernization-factory.git
cd ai-modernization-factory
```

Create a Python 3.12 virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install the project in editable mode:

```bash
pip install -e ".[dev]"
```

Verify the CLI:

```bash
ai-factory --help
ai-factory version
```

Run tests:

```bash
pytest
```

Run quality checks:

```bash
ruff check .
ruff format --check .
mypy src
```

## Current Status

The project foundation is complete.

Current capabilities include:

* Python 3.12 project setup
* Editable package installation
* Typer-based CLI
* Version command
* Automated CLI tests
* Project documentation
* Architecture decisions
* Public GitHub repository

The next implementation milestone is the first end-to-end analysis pipeline:

```text
Repository Intelligence
    +
Issue Detection
    +
Recommendations
    +
Modernization Report
```

## Success Criteria for the MVP

The MVP will be considered successful when a user can run:

```bash
ai-factory analyze ./sample-app
```

and receive:

* A structured application inventory
* Evidence-based findings
* Prioritized issues
* Actionable recommendations
* A modernization assessment report
* A small-model-generated executive summary
* Model usage, latency, and cost information
* A working deterministic report when AI is disabled

## Long-Term Goal

The long-term goal is to create a production-grade AI modernization platform that helps organizations:

* Understand legacy applications
* Identify technical debt
* Assess security and maintainability risks
* Prioritize modernization investments
* Generate practical modernization roadmaps
* Refactor applications safely
* Measure modernization progress
* Route AI tasks to the lowest-cost model that meets quality requirements
* Detect quality regressions
* Continuously optimize model usage and cost

## Contributing

Contributions are welcome.

Before contributing, review:

* `docs/architecture.md`
* `docs/coding-standards.md`
* `docs/contribution.md`
* `docs/decisions/`

All changes should include appropriate tests and documentation.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

Satish Nampally

GitHub: https://github.com/sknampally
