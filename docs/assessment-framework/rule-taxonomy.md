# Rule Taxonomy

Hierarchical control areas for future Shared Rule packs. Identifiers are stable
and machine-safe (`parent.child`). These nodes are **methodology metadata**, not
executable rules.

## Conventions

- **identifier:** `area.kebab-subarea` (aligns with Shared Rule ID namespaces)
- **parent:** taxonomy parent ID or dimension ID
- **severity range:** typical technical severity band (not automatic assignment)
- **applicability:** `community`, `enterprise`, or `both`

Evidence expectations describe what a future rule should cite. No YAML executable
rules are defined here.

---

## Architecture

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `architecture.dependency-structure` | Dependency Structure | architecture | Direction, fan-in/out, cycles among modules/packages | medium–critical | both |
| `architecture.layering` | Layering | architecture | Declared or conventional layer violations | medium–high | both |
| `architecture.modularity` | Modularity | architecture | Module/package cohesion and extraction readiness | low–high | both |
| `architecture.boundaries` | Boundaries | architecture | Explicit API/module boundaries and leakage | medium–high | both |
| `architecture.coupling` | Coupling | architecture | Excessive coupling between components | medium–high | both |
| `architecture.cohesion` | Cohesion | architecture | Mixed responsibilities within a unit | low–medium | both |
| `architecture.api-design` | API Design | architecture | API surface consistency and versioning signals | low–high | both |
| `architecture.data-access` | Data Access | architecture | Persistence access patterns and leakage | medium–high | both |
| `architecture.integration-architecture` | Integration Architecture | architecture | External system coupling patterns | medium–high | both |
| `architecture.service-architecture` | Service Architecture | architecture | Service boundaries (repo + enterprise services) | medium–high | both |
| `architecture.enterprise-standards` | Enterprise Standards | architecture | Alignment to declared architecture standards | low–high | enterprise |

**Evidence expectations:** Repository Graph edges, package paths, framework
markers, Enterprise application/service links when declared.

---

## Maintainability

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `maintainability.complexity` | Complexity | maintainability | Cyclomatic/cognitive complexity heuristics | low–high | both |
| `maintainability.duplication` | Duplication | maintainability | Repeated logic/blocks | low–medium | both |
| `maintainability.size` | Size | maintainability | Oversized files/modules/classes | low–medium | both |
| `maintainability.readability` | Readability | maintainability | Naming/structure signals (bounded) | informational–low | both |
| `maintainability.documentation` | Documentation | maintainability | Missing or stale essential docs | low–medium | both |
| `maintainability.change-concentration` | Change Concentration | maintainability | Hotspot concentration when history available | medium–high | both |
| `maintainability.configuration-complexity` | Configuration Complexity | maintainability | Config sprawl and env coupling | low–medium | both |

---

## Technical Debt

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `technical-debt.deprecated-technology` | Deprecated Technology | technical-debt | EOL/deprecated platform usage | medium–critical | both |
| `technical-debt.unsupported-dependencies` | Unsupported Dependencies | technical-debt | Dependencies outside support windows | medium–high | both |
| `technical-debt.upgrade-risk` | Upgrade Risk | technical-debt | Version gaps that block upgrades | medium–high | both |
| `technical-debt.build-debt` | Build Debt | technical-debt | Fragile/legacy build tooling | low–high | both |
| `technical-debt.migration-blockers` | Migration Blockers | technical-debt | Patterns that block target platforms | medium–critical | both |
| `technical-debt.legacy-framework-usage` | Legacy Framework Usage | technical-debt | Legacy framework stacks still in use | medium–high | both |

---

## Security

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `security.secrets` | Secrets | security | Credential-like material in repo | high–critical | both |
| `security.authentication` | Authentication | security | Auth configuration and library usage | medium–critical | both |
| `security.authorization` | Authorization | security | Access-control signals | medium–critical | both |
| `security.input-validation` | Input Validation | security | Validation gaps (heuristic) | medium–high | both |
| `security.injection-risk` | Injection Risk | security | Injection-prone patterns | high–critical | both |
| `security.cryptography` | Cryptography | security | Weak crypto usage signals | medium–critical | both |
| `security.transport-security` | Transport Security | security | TLS/HTTP security config | medium–high | both |
| `security.configuration` | Configuration | security | Insecure defaults in config | medium–high | both |
| `security.dependency-risk` | Dependency Risk | security | Known vulnerable dependencies (imported) | medium–critical | both |

---

## Performance and Scalability

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `performance.blocking-operations` | Blocking Operations | performance | Blocking calls on likely request paths | medium–high | both |
| `performance.query-patterns` | Query Patterns | performance | Suspicious query/access patterns | medium–high | both |
| `performance.caching` | Caching | performance | Missing/misused cache signals | low–medium | both |
| `performance.concurrency` | Concurrency | performance | Concurrency anti-patterns | medium–high | both |
| `performance.serialization` | Serialization | performance | Costly serialization patterns | low–medium | both |
| `performance.resource-management` | Resource Management | performance | Resource leak/lifetime signals | medium–high | both |
| `performance.hot-path-coupling` | Hot-Path Coupling | performance | Heavy coupling on entry paths | medium–high | both |

---

## Reliability and Resilience

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `reliability.error-handling` | Error Handling | reliability | Absent/unsafe error handling | medium–high | both |
| `reliability.retry-behavior` | Retry Behavior | reliability | Retry presence/absence | low–medium | both |
| `reliability.timeout-behavior` | Timeout Behavior | reliability | Timeout configuration signals | medium–high | both |
| `reliability.circuit-breaking` | Circuit Breaking | reliability | Circuit breaker usage | low–medium | both |
| `reliability.transaction-boundaries` | Transaction Boundaries | reliability | Transaction scope signals | medium–high | both |
| `reliability.failure-isolation` | Failure Isolation | reliability | Blast-radius structural signals | medium–high | both |
| `reliability.idempotency` | Idempotency | reliability | Idempotency patterns for handlers | low–medium | both |

---

## Cloud and Platform Readiness

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `cloud.externalized-configuration` | Externalized Configuration | cloud | Config externalization | medium–high | both |
| `cloud.statelessness` | Statelessness | cloud | Local state / sticky session signals | medium–high | both |
| `cloud.portability` | Portability | cloud | Environment coupling | medium–high | both |
| `cloud.container-readiness` | Container Readiness | cloud | Container/runtime packaging | low–medium | both |
| `cloud.managed-service-compatibility` | Managed Service Compatibility | cloud | Cloud service client patterns | informational–medium | both |
| `cloud.deployment-automation` | Deployment Automation | cloud | CI/CD and deploy automation | medium–high | both |

---

## AI Enablement Readiness

| ID | Title | Parent | Definition | Severity range | Edition |
| -- | ----- | ------ | ---------- | -------------- | ------- |
| `ai-enablement.api-accessibility` | API Accessibility | ai-enablement | Machine-consumable APIs | low–medium | both |
| `ai-enablement.data-accessibility` | Data Accessibility | ai-enablement | Structured data access paths | low–medium | both |
| `ai-enablement.metadata-quality` | Metadata Quality | ai-enablement | Schema/docs/metadata richness | low–medium | both |
| `ai-enablement.event-availability` | Event Availability | ai-enablement | Events/messages for automation | informational–medium | both |
| `ai-enablement.security-boundaries` | Security Boundaries | ai-enablement | Authz boundaries for tools/agents | medium–high | both |
| `ai-enablement.integration-readiness` | Integration Readiness | ai-enablement | Integration hooks for AI workflows | low–medium | both |
| `ai-enablement.knowledge-accessibility` | Knowledge Accessibility | ai-enablement | Docs/knowledge usable by agents | low–medium | both |
| `ai-enablement.mcp-tooling-readiness` | MCP or Tooling Readiness | ai-enablement | MCP/tool server readiness signals | informational–medium | both |

---

## Related dimensions

Taxonomy nodes map to dimensions in [dimensions.md](dimensions.md). A single
finding may contribute to multiple dimensions via explicit mapping metadata in
future rule packs—not by silent inference.
