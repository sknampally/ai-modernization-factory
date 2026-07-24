# Assembly

```text
AssessmentService
  → Shared Rule / architecture pack execution (existing)
  → ArchitectureConclusionService (optional)
  → ArchitectureAssessmentAssembler
  → architecture-assessment.json
```

The assembler does not re-run architecture rules or parsing.
It consumes in-memory findings and optional conclusion results.
