# Architecture Report Domain Model

Section ID: `report.architecture`  
Section version: `1.0.0`

`ArchitectureReportSection` is a presentation-focused model. Templates must not
bind directly to `ArchitectureAssessmentSection`.

Key fields:

- status / status_label / status_summary
- executive_summary
- key_metrics
- coverage_summary
- conclusions / findings / recommendation_groups
- strengths / limitations
- traceability_summary
- architecture_pack_id / architecture_pack_version
- generated_from_assessment_section_version
- enterprise_context_used
- metadata (bounded fingerprints only)

Versions remain separate:

| Layer | Version field | Current |
| ----- | ------------- | ------- |
| Architecture pack | pack version | 1.0.0 |
| Assessment section | section_version | 1.0.0 |
| Report section | section_version | 1.0.0 |
| report.json schema | schema_version | 1.2 (optional additive key) |
