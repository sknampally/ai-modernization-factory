# AI enrichment

Optional one-call narrative over deterministic findings and recommendations.

```text
findings.json + recommendations.json + compact repo summary
        ↓
AI Enrichment (exactly one Bedrock Converse call)
        ↓
ai-enrichment.json
```

## Boundary

| Allowed | Forbidden |
| ------- | --------- |
| Interpretive narrative | Creating or deleting findings |
| Referencing known finding/recommendation IDs | Mutating `findings.json` / `recommendations.json` |
| Compact budgeted context | Full graph dumps, source files, secrets |

## Call budget

* Deterministic mode: **0** provider calls
* `--with-ai`: **exactly 1** provider call
* No silent retries that create additional calls

## Failure behavior

Enrichment failures become staged warnings. Deterministic graphs, findings,
recommendations, and reports remain valid. No fabricated enrichment is written.
CLI exit code remains 0 for enrichment-only failure.

## Artifact

`ai-enrichment.json` (written only on successful enrichment).

See also [architecture/ai-enrichment.md](architecture/ai-enrichment.md) and
[report-generation.md](report-generation.md).
