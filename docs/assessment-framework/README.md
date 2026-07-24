# CodeStrata Assessment Framework

**Milestone:** Phase 4.1.2 — methodology and contracts (complete as documentation).

This framework guides future rule packs, scoring, recommendations, modernization
prioritization, and CTO-facing reports. It does **not** imply that production
scoring, dimension packs, or a CTO report are already implemented.

```text
Executive Question
    → Assessment Dimension
    → Assessment Principle
    → Control / Evaluation Area
    → Rule
    → Evidence
    → Finding
    → Recommendation
    → Score
    → Business Risk
    → Modernization Initiative
    → CTO Report Section
```

## Documents in this folder

| Document | Topic |
| -------- | ----- |
| [methodology.md](methodology.md) | Principles and assessment states |
| [dimensions.md](dimensions.md) | Assessment dimensions |
| [rule-taxonomy.md](rule-taxonomy.md) | Hierarchical rule taxonomy |
| [evidence-and-confidence.md](evidence-and-confidence.md) | Evidence origins, strength, confidence |
| [severity-and-business-impact.md](severity-and-business-impact.md) | Severity, business impact, priority |
| [scoring.md](scoring.md) | Transparent scoring methodology |
| [coverage.md](coverage.md) | Coverage vs confidence vs score |
| [positive-evidence.md](positive-evidence.md) | Strengths and good practices |
| [recommendations.md](recommendations.md) | Recommendation hierarchy |
| [modernization-prioritization.md](modernization-prioritization.md) | Waves and initiatives |
| [report-structure.md](report-structure.md) | CTO Assessment Report outline |
| [executive-narrative.md](executive-narrative.md) | Executive summary and language |
| [community-enterprise-boundary.md](community-enterprise-boundary.md) | Product editions |
| [traceability.md](traceability.md) | Statement → evidence chain |
| [limitations.md](limitations.md) | What static analysis cannot prove |
| [examples.md](examples.md) | Worked examples |

## Relationship to the platform today

| Capability | Status relative to this framework |
| ---------- | --------------------------------- |
| Repository assessment (`aimf assess`) | Available; unchanged by this milestone |
| Phase 3 findings / recommendations | Available; IDs and semantics preserved |
| Current HTML Engineering Assessment | Available; not redesigned here |
| Shared Rule Platform (4.1 / 4.1.1) | Infrastructure ready for future packs |
| Dimension scoring / CTO report | **Designed here; not implemented** |
| Architecture / TD / Security / Perf packs | Deferred to Phase 4.2+ |

## Core principles (summary)

1. Evidence before judgment.
2. Deterministic analysis before AI interpretation.
3. Scores must be explainable; never hide severe findings.
4. Missing evidence ≠ poor quality; no findings ≠ excellence.
5. Technical severity ≠ business impact ≠ priority.
6. Repository facts and enterprise facts remain distinguishable.
7. Enterprise context is optional; repository-only assessment remains valid.
8. Every report statement is observed, inferred, declared, unavailable, or not assessed.

See [methodology.md](methodology.md) for the full principle set.
