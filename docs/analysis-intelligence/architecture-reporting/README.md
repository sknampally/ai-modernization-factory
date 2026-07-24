# Architecture CTO Report Integration

Phase **4.2.5** — Architecture CTO Report Integration.

Consumes the existing `ArchitectureAssessmentSection` and presents it in
`report.json` and the HTML report. The assessment artifact remains the source
of truth. The report adapter does not recompute findings, conclusions, or
recommendations.

| Concept | Meaning |
| ------- | ------- |
| Finding | Specific detected repository condition |
| Conclusion | Deterministic interpretation of related findings |
| Assessment section | Structured evaluation of one engineering dimension |
| Report section | Audience-oriented presentation of assessment data |
| Executive summary | Deterministic bounded presentation, not a new analysis |

Disabled by default: `[report.sections.architecture] enabled = false`.

When disabled, report output shape is unchanged (schema remains `1.2`).

## Documents

- [architecture-report-model.md](architecture-report-model.md)
- [assessment-adapter.md](assessment-adapter.md)
- [executive-summary.md](executive-summary.md)
- [conclusions.md](conclusions.md)
- [findings.md](findings.md)
- [recommendations.md](recommendations.md)
- [coverage.md](coverage.md)
- [limitations.md](limitations.md)
- [strengths.md](strengths.md)
- [traceability.md](traceability.md)
- [html-section.md](html-section.md)
- [report-json.md](report-json.md)
- [configuration.md](configuration.md)
- [cli.md](cli.md)
- [mcp.md](mcp.md)
- [compatibility.md](compatibility.md)
- [limitations-and-future-work.md](limitations-and-future-work.md)
- [examples.md](examples.md)
