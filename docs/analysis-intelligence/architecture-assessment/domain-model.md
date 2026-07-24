# Domain model

`ArchitectureAssessmentSection` (`section_id = assessment.architecture`,
`section_version = 1.0.0`) holds:

- status and pack/version
- fingerprints (graph, evidence, configuration)
- execution summary
- coverage areas
- finding references (not duplicated full findings)
- conclusions and recommendation groups (optional)
- empty strengths until positive evidence exists
- structured limitations
- machine-readable traceability index
- diagnostics

Business impact remains `unknown` for repository-only assessments.
