# Executive Narrative and Report Language

## One-page executive summary

Must answer:

1. What was assessed?
2. What is the overall condition (band + confidence + coverage)?
3. What is working well? (3–5 strengths)
4. What are the top material risks? (3–5)
5. What requires immediate attention?
6. Is modernization feasible?
7. What should leadership do next?
8. What are important limitations?

### Suggested elements

- assessment scope (repo / apps / time / engines)
- overall assessment band
- 3–5 strengths (evidence-backed)
- 3–5 material risks
- modernization readiness
- recommended first actions
- confidence and coverage
- limitations

The summary must **not** become a lint inventory.

## Narrative quality

| Weak | Better | Best (with enterprise context) |
| ---- | ------ | ------------------------------ |
| “43 deprecated dependencies were found.” | “The application relies on multiple unsupported dependencies, increasing maintenance risk and raising upgrade effort.” | “A business-critical application supporting Student Registration relies on multiple unsupported dependencies, creating near-term maintenance risk ahead of the planned cloud migration.” |

Every narrative statement needs traceability (see [traceability.md](traceability.md)).

## Writing standards

**Use**

- clear business language
- direct, bounded conclusions
- evidence-backed claims
- explicit uncertainty
- action-oriented recommendations
- short paragraphs and meaningful headings

**Avoid**

- raw rule names in executive sections
- unexplained jargon
- inflated or fear-based language
- fake precision (costs, dates without models)
- generic AI-generated prose
- long finding lists in the main body

Detailed findings belong in appendices.

## AI narratives (future)

Optional AI enrichment may help drafting, but:

- must not invent findings
- must cite finding/recommendation IDs
- must not break the observed/inferred/declared labels
- must not change deterministic artifacts (`findings.json`, etc.)

No AI narrative is added by this milestone.
