# Assessment Methodology

## Intent

**CodeStrata Community** helps developers and small teams understand a
repository, identify credible engineering risks, and act on local
recommendations.

**CodeStrata Enterprise** helps engineering leaders understand portfolios,
connect findings to business systems, prioritize investment, and govern
standards.

One methodology serves both. Repository-only assessment remains valid.
Enterprise context remains optional enrichment.

## Traceability chain

```text
Executive Question
    ↓
Assessment Dimension
    ↓
Assessment Principle / Control Area
    ↓
Rule (stable ID + version)
    ↓
Evidence (origin + strength + provenance)
    ↓
Finding (observed condition)
    ↓
Recommendation (potential action)
    ↓
Score (with coverage + confidence)
    ↓
Business Risk / Priority
    ↓
Modernization Initiative / Wave
    ↓
CTO Report Section
```

## Statement classifications

Every claim in a report or narrative must be one of:

| Label | Meaning |
| ----- | ------- |
| **observed** | Directly extracted from repository artifacts |
| **derived** | Deterministically calculated from observed evidence |
| **declared** | Provided by metadata/config; not independently verified |
| **inferred** | Reasonable conclusion with explicit uncertainty |
| **unavailable** | Needed evidence was not present |
| **not assessed** | Dimension or control was out of scope for this run |

Do not present inferred or declared facts as observed.

## Assessment outcomes for a control or area

| Outcome | Meaning |
| ------- | ------- |
| `strong` | Positive evidence of good practice |
| `adequate` | Meets expectations without notable risk |
| `needs_attention` | Material issues exist; remediation advised |
| `weak` | Significant deficiencies |
| `critical` | Severe conditions requiring urgent attention |
| `not_assessed` | Not in scope or unsupported |
| `insufficient_evidence` | In scope, but evidence too thin to score |

Absence of matched findings must **not** auto-promote an area to `strong`.

## Principles

1. **Evidence before judgment.** No score or narrative without cited evidence or an explicit “not assessed / unavailable” label.
2. **Deterministic analysis before AI.** AI may interpret later; it must not invent findings or break traceability.
3. **Explainable scores.** Every score answers why, what evidence, what was not assessed, what would change it.
4. **Missing evidence is not failure.** Prefer `insufficient_evidence` / `not_assessed` over punitive zeros.
5. **No findings ≠ excellence.** Coverage and positive evidence are required to claim strength.
6. **Confidence and coverage accompany every score.**
7. **Technical severity and business impact are separate.**
8. **Repository vs enterprise provenance stays distinct.**
9. **Findings describe observed conditions;** recommendations describe actions.
10. **Priorities consider dependencies and (when available) business context.**
11. **Do not claim runtime, production, cost, or organizational facts that static analysis cannot prove.**
12. **No opaque weighted averages** without documented rationale.
13. **Severe findings must not be hidden** by averages.
14. **Executive summaries must not exaggerate certainty.**

## Current product honesty

Today CodeStrata produces repository inventory, graphs, deterministic findings,
recommendations, and an Engineering Assessment HTML report. Dimension scoring,
business-impact scoring, and the full CTO report structure defined here are
**methodology targets**, not current runtime behavior.

`aimf assess` remains unchanged by this framework milestone.
