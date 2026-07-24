# Assessment-to-Report Adapter

`ArchitectureReportAdapter` is the single boundary from assessment domain to
report presentation.

Responsibilities:

- status mapping
- executive summary templates
- bounded metrics
- conclusion / finding / recommendation view models
- coverage wording
- limitation grouping
- bounded traceability summary

Does not:

- re-run architecture analysis
- regenerate conclusions or recommendation groups
- mutate canonical findings
- embed source code or absolute paths
- invent scores, grades, or business impact

Prefer in-memory `ArchitectureAssessmentSection` during assess. Do not read
`architecture-assessment.json` back from disk when the in-memory section is
available.
