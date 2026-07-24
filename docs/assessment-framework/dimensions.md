# Assessment Dimensions

Stable identifiers use `dimension.<slug>`.

Each dimension answers an **executive question** and one or more **engineering
questions**. Only some aspects are observable from static repository analysis.

## Dimension catalog

| ID | Title | Community | Enterprise |
| -- | ----- | --------- | ---------- |
| `dimension.architecture` | Architecture | Primary | Enriched |
| `dimension.maintainability` | Maintainability | Primary | Enriched |
| `dimension.technical-debt` | Technical Debt | Primary | Enriched |
| `dimension.security` | Security | Primary | Enriched |
| `dimension.performance-scalability` | Performance and Scalability | Partial | Enriched |
| `dimension.reliability-resilience` | Reliability and Resilience | Partial | Enriched |
| `dimension.testability-quality` | Testability and Quality Engineering | Primary | Enriched |
| `dimension.operability-observability` | Operability and Observability | Partial | Enriched |
| `dimension.cloud-platform-readiness` | Cloud and Platform Readiness | Primary | Enriched |
| `dimension.data-integration` | Data and Integration Architecture | Partial | Enriched |
| `dimension.developer-experience` | Developer Experience | Primary | Enriched |
| `dimension.modernization-readiness` | Modernization Readiness | Primary | Enriched |
| `dimension.ai-enablement` | AI Enablement Readiness | Emerging | Enriched |

**Partial** means useful static signals exist, but many conclusions require
runtime or organizational evidence. **Emerging** means methodology is defined;
rule coverage is expected later.

---

## 1. Architecture (`dimension.architecture`)

**Purpose:** Assess structure, boundaries, and dependency control.

**Executive question:** Can this system evolve without disproportionate cost and risk?

**Engineering questions:** Are dependencies controlled? Are boundaries explicit?
Are components modular? Are cyclic dependencies present?

**Observable statically:** Dependency graph, package/module structure, framework
usage, repository graph, layered naming conventions, API surface files.

**Requires runtime/org evidence:** Team coordination cost, deployment frequency,
production incident correlation, true scalability.

**Candidate subdimensions:** dependency-structure, layering, modularity,
boundaries, coupling, cohesion, api-design, data-access, integration,
service-architecture.

**Evidence sources:** Repository Graph, Engineering Knowledge Graph, Assessment
Graph, manifests, lockfiles; Enterprise relationships when present.

**Example future rules:** Cyclic package dependencies; layering violations;
unbounded fan-out.

**Report outputs:** Architecture section, material structural risks, strengths.

**Limitations:** Static structure ≠ runtime topology. Missing modules may be
generated or external.

**Edition relevance:** Core Community signal; Enterprise adds application /
capability impact.

---

## 2. Maintainability (`dimension.maintainability`)

**Purpose:** Assess how hard the codebase is to understand and change safely.

**Executive question:** How expensive is ongoing change likely to be?

**Engineering questions:** Complexity, size, duplication, documentation,
configuration sprawl, change concentration (when history available).

**Observable statically:** File/module size, complexity heuristics, duplication
signals, docs presence, config file sprawl.

**Not alone:** Actual team velocity, cognitive load, onboarding time.

**Subdimensions:** complexity, duplication, size, readability, documentation,
change-concentration, configuration-complexity.

---

## 3. Technical Debt (`dimension.technical-debt`)

**Purpose:** Identify deferred technology and upgrade risk.

**Executive question:** What accumulated debt constrains future investment?

**Engineering questions:** Deprecated tech, unsupported deps, upgrade blockers,
legacy frameworks, build debt.

**Observable statically:** Dependency versions, EOL catalogs (when declared),
build tool vintage, framework versions.

**Not alone:** Exact remediation cost or calendar duration.

**Subdimensions:** deprecated-technology, unsupported-dependencies, upgrade-risk,
build-debt, migration-blockers, legacy-framework-usage.

---

## 4. Security (`dimension.security`)

**Purpose:** Surface security-relevant conditions from static evidence.

**Executive question:** Where are the most credible security exposures in code and config?

**Engineering questions:** Secrets in repo, auth patterns, input validation
signals, dependency CVEs (when imported), transport configuration.

**Observable statically:** Config/secret patterns, dependency advisories (import),
auth library usage, insecure defaults in files.

**Not alone:** Actual exploitability, production posture, SOC compliance.

**Subdimensions:** secrets, authentication, authorization, input-validation,
injection-risk, cryptography, transport-security, configuration, dependency-risk.

**Language rule:** Prefer “evidence indicates a potential exposure” over “the
system is insecure/secure.”

---

## 5. Performance and Scalability (`dimension.performance-scalability`)

**Purpose:** Flag structural patterns that often impede scale.

**Executive question:** Are there structural risks to performance or scale?

**Engineering questions:** Blocking patterns, N+1-like query shapes (heuristic),
caching libraries, hot-path coupling.

**Observable statically:** Limited pattern matches; library usage.

**Not alone:** Production latency, capacity, real hotspots without profiles.

**Default honesty:** Many controls remain `not_assessed` or
`insufficient_evidence` without runtime imports.

---

## 6. Reliability and Resilience (`dimension.reliability-resilience`)

**Purpose:** Assess failure-handling design signals.

**Executive question:** How deliberately does the system handle failure?

**Observable statically:** Retry/timeout libraries, error-handling patterns,
transaction annotations (language-specific).

**Not alone:** Production MTTR, incident rates, chaos outcomes.

---

## 7. Testability and Quality Engineering (`dimension.testability-quality`)

**Purpose:** Assess automated quality foundations.

**Executive question:** Can the team change this system with confidence?

**Observable statically:** Test file presence/layout, frameworks, CI test steps
(when present), coverage config (declared, not measured unless imported).

**Not alone:** True coverage %, flaky-test rates, quality of assertions.

---

## 8. Operability and Observability (`dimension.operability-observability`)

**Purpose:** Assess run/operate readiness signals in repo.

**Executive question:** Can operators see and manage this system?

**Observable statically:** Logging/metrics/tracing libraries, health endpoints,
runbooks in docs, deployment manifests.

**Not alone:** Actual dashboard quality, alert noise, on-call load.

---

## 9. Cloud and Platform Readiness (`dimension.cloud-platform-readiness`)

**Purpose:** Assess portability and cloud-friendly design signals.

**Executive question:** How ready is this application for cloud platforms?

**Observable statically:** Externalized config, container files, twelve-factor
signals, managed-service client usage, IaC presence.

**Not alone:** Actual cloud cost, multi-AZ resilience, org cloud policy fit.

---

## 10. Data and Integration Architecture (`dimension.data-integration`)

**Purpose:** Assess data stores, APIs, and integration coupling.

**Executive question:** Are data and integrations structured for change?

**Observable statically:** ORM usage, multiple DB clients, message libraries,
OpenAPI files (metadata), enterprise DataStore/API links when declared.

**Not alone:** Production data quality, schema drift, SLA of external systems.

---

## 11. Developer Experience (`dimension.developer-experience`)

**Purpose:** Assess local build/run/onboarding friction signals.

**Executive question:** How hard is it for engineers to be productive here?

**Observable statically:** README quality, wrappers, editorconfig, scripts,
consistent tooling.

**Not alone:** Actual onboarding days, developer satisfaction.

---

## 12. Modernization Readiness (`dimension.modernization-readiness`)

**Purpose:** Synthesize feasibility of change and upgrade.

**Executive question:** Is modernization feasible, and where should it start?

**Observable statically:** Composite of debt, architecture, tests, build, CI;
roadmap inputs from findings.

**Enterprise enrichment:** Criticality, initiatives, ownership, capability risk.

**Not alone:** Budget, org capacity, political constraints.

---

## 13. AI Enablement Readiness (`dimension.ai-enablement`)

**Purpose:** Assess whether systems can safely expose capabilities to AI tooling.

**Executive question:** Can AI agents and tools interact with this system safely and usefully?

**Observable statically:** API surface, auth boundaries, event/message presence,
MCP/tooling configs, metadata quality signals.

**Not alone:** Data governance approval, model risk, production AI incidents.

**Status:** Methodology defined; production rule packs deferred.

---

## Cross-cutting notes

- Dimensions may share evidence; scores remain per-dimension with shared finding
  references.
- A dimension with low coverage must not display a misleading strong band.
- Future Phase 4.2+ packs map primarily into Architecture, Technical Debt,
  Security, Performance, then Modernization Intelligence.
