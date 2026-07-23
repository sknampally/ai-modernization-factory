"""Integrated runtime: Phase 1 assessment + Phase 2/3 graph pipeline.

```text
CLI / Config
     ↓
Existing Phase 1 Analysis
     ↓
Phase 1 → Phase 2 Adapter
     ↓
Repository Inventory
     ↓
Repository Graph
     ↓
Knowledge Pipeline ← Engineering Knowledge Graph (builtin catalog)
     ↓
KnowledgeBindingResult
     ↓
Assessment Graph
     ↓
Rule Engine → Findings (findings.json)
     ↓
Recommendation Engine → Recommendations (recommendations.json)
     ↓
Artifact Writer (reports/<repo>/<run>/graphs/)
     ↓
Existing Report / Optional AI
```

## Coexistence

Phase 1 remains the supported assessment path for technology detection, findings,
deterministic recommendations, HTML/JSON reports, and optional Bedrock AI.

Phase 2/3 adds graph-based knowledge context for the same assessment run:

* **Repository Inventory** — repository-relative file facts and fingerprints
* **Repository Graph** — structural projection of that inventory (including dependencies)
* **Engineering Knowledge Graph** — reusable, repository-independent catalog
* **Knowledge Bindings** — deterministic observation→concept links
* **Assessment Graph** — assessment-scoped reference projection of accepted bindings
* **Rule Engine** — deterministic findings from Assessment Graph context
* **Recommendation Engine** — deterministic actions derived from those findings

AI enrichment remains optional and separate; recommendation JSON is not yet passed
into the AI context.

## Boundaries

* Phase 1 ``Repository`` / ``RepositoryFacts`` stay scanner and analyzer DTOs.
* Phase 2 ``RepositoryManifest`` / ``RepositoryGraph`` stay inventory and graph
  contracts. They are adapted from Phase 1 outputs, not collapsed into them.
* The Engineering Knowledge Graph never receives repository identity.
* The Assessment Graph owns assessment-scoped links only.
* Rules and recommendation providers never mutate RG, EKG, AG, bindings, or findings.

## AI boundary

Graph construction, rule evaluation, recommendation derivation, and artifact
persistence run before optional AI and do not invoke providers. AI continues to
use the existing normalized context contract; full graph JSON and recommendation
JSON are not sent to the model in this milestone.
