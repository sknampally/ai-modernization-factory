# Assess runtime

How `aimf assess` produces graphs, findings, recommendations, optional AI
enrichment, and reports.

```text
CLI / Config
     ↓
Phase 1 Analysis (detect + analyzers + optional PMD)
     ↓
Repository Inventory
     ↓
Repository Graph (+ dependency extraction)
     ↓
Knowledge Pipeline ← Engineering Knowledge Graph (builtin catalog)
     ↓
Assessment Graph
     ↓
Rule Engine → findings.json
     ↓
Recommendation Engine → recommendations.json
     ↓
optional AI Enrichment (exactly one provider call) → ai-enrichment.json
     ↓
HTML Report v2 (report.html) + report.json
     (+ optional ai-execution.json)
```

## Modes

| Mode | AI calls | Notes |
| ---- | -------- | ----- |
| Deterministic (`--no-ai`, default) | 0 | Graphs, findings, recommendations, HTML/JSON |
| AI (`--with-ai`) | 1 | Same deterministic artifacts + enrichment on success |

## Failure behavior

* Graph / rule / recommendation failures abort the assessment with a clear stage error.
* AI enrichment failures warn and keep deterministic artifacts; CLI exits 0.
* HTML/JSON write failures surface as report-stage errors without deleting prior
  graph/findings/recommendation/enrichment files already written for the run.

## Related docs

* [repository-graph.md](repository-graph.md)
* [assessment-graph.md](assessment-graph.md)
* [rule-engine.md](rule-engine.md)
* [recommendation-engine.md](recommendation-engine.md)
* [ai-enrichment.md](ai-enrichment.md)
* [report-generation.md](report-generation.md)
