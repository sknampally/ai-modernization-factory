# Technical Debt CTO Report Integration

Phase **4.3.6** — Technical Debt CTO Report Integration.

Consumes the existing in-memory `TechnicalDebtAssessmentSection` and presents it
in `report.json` and the HTML report. The assessment artifact remains the source
of truth. The report adapter does **not** collect evidence, evaluate rules,
re-read artifacts, or generate AI inference.

| Concept | Meaning |
| ------- | ------- |
| Assessment section | `assessment.technical_debt` (@1.2.0) with inventory, synthesis, coverage |
| Report section | `report.technical_debt` (@1.0.0) audience-oriented projection |
| Executive summary | Deterministic templates from assessment facts only |
| Hotspot order | Inventory order (severity → count → path) — presentation, not priority |

Disabled by default: `[report.sections.technical_debt] enabled = false`.

When disabled, report output shape is unchanged (schema remains `1.2`; no
`assessment.technical_debt` key in `report.json`).

## Enable

```toml
[report.sections.technical_debt]
enabled = true
```

Requires a technical debt assessment section for the run (typically
`[assessment.sections.technical_debt] enabled = true` with the debt pack and
complexity evidence enabled). Prefer the in-memory assessment section during
orchestration; adapter failures are isolated so other report sections continue.

## JSON

Additive under `assessment.technical_debt` in `report.json`:

- status / status_label / status_summary
- executive_summary
- key_metrics (production findings, hotspots shown, themes, conclusions, coverage, separate test findings)
- significant_themes (production themes with findings)
- top_production_hotspots (bounded; presentation order noted)
- conclusions / recommendations (production-facing; test audience excluded)
- test_observation (separate test-maintainability block)
- coverage_summary / limitations / traceability_summary

## HTML

Section id `technical-debt-assessment`, rendered after Architecture (when both
present). Test-maintainability observation is visually distinct from production
content.

## Explicit non-goals

- Composite debt or maintainability scores
- Synthetic priority formulas
- Financial, remediation-hour, velocity, or business-impact estimates
- AI-generated conclusions or recommendations
- Re-analysis in the adapter
