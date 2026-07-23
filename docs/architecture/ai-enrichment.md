# AI enrichment over deterministic findings and recommendations

```text
Repository Graph
        ↓
Assessment Graph
        ↓
Rule Engine → Findings
        ↓
Recommendation Engine → Recommendations
        ↓
AI Enrichment (one provider call)
        ↓
ai-enrichment.json (+ existing HTML/JSON reports)
```

Deterministic findings and recommendations remain the source of truth. AI must
not create, delete, or modify those artifacts.

## One-call boundary

* Deterministic mode: zero provider calls
* `--with-ai`: exactly one provider call
* No silent retries that create additional calls

## Compact context

The enrichment prompt receives a budgeted, sorted JSON context with repository
identity, technology/dependency summaries, finding summaries, and recommendation
summaries. It excludes full graph JSON, source files, secrets, and absolute paths.

## Traceability

`AiEnrichmentResult` carries referenced finding and recommendation IDs. Unknown
IDs are rejected during validation.

## Failure behavior

AI enrichment failures surface as staged warnings. Deterministic graphs,
findings, recommendations, and HTML/JSON reports remain valid. No fabricated
fallback enrichment content is written. The CLI completes successfully (exit 0)
with an AI warning; enrichment failure alone does not force a non-zero exit.

## Current limitations

* No agent framework or multi-step tool use
* No MCP integration
* Enrichment narrative is not merged into `findings.json` or `recommendations.json`
* Phase 1 HTML/JSON reports still consume a bridged AI recommendation contract
  for display compatibility
