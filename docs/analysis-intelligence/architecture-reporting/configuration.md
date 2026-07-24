# Configuration

```toml
[report.sections.architecture]
enabled = false
include_executive_summary = true
include_metrics = true
include_conclusions = true
include_recommendation_groups = true
include_findings = true
include_coverage = true
include_limitations = true
include_traceability = true
include_strengths = true
```

Default is disabled. Enabling report architecture does **not** auto-enable
rules, evidence providers, conclusions, or assessment section assembly.

If report architecture is enabled but assessment is absent, the report continues
without the architecture section (warning emitted).
