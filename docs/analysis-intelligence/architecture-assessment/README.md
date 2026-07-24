# Architecture Assessment Integration

Phase **4.2.4** — Architecture Assessment Integration.

Makes Architecture Intelligence a first-class optional section of the formal
assessment result without redesigning the HTML or CTO report.

| Concept | Meaning |
| ------- | ------- |
| Assessment | Complete structured engineering evaluation |
| Assessment section | Bounded evaluation of one engineering dimension |
| Finding | Specific detected condition |
| Conclusion | Deterministic interpretation of related findings |
| Recommendation group | Coordinated response |
| Report | Audience-specific presentation of assessment data |

Disabled by default: `[assessment.sections.architecture] enabled = false`.

When disabled, assessment output shape is unchanged.

Phase 4.2.5 presents this section in customer reports when
`[report.sections.architecture] enabled = true`. See
[../architecture-reporting/README.md](../architecture-reporting/README.md).

## Documents

- [domain-model.md](domain-model.md)
- [statuses.md](statuses.md)
- [assembly.md](assembly.md)
- [coverage.md](coverage.md)
- [findings.md](findings.md)
- [conclusions.md](conclusions.md)
- [recommendations.md](recommendations.md)
- [strengths.md](strengths.md)
- [limitations.md](limitations.md)
- [traceability.md](traceability.md)
- [schema-and-versioning.md](schema-and-versioning.md)
- [artifacts.md](artifacts.md)
- [configuration.md](configuration.md)
- [cli.md](cli.md)
- [mcp.md](mcp.md)
- [limitations-and-future-work.md](limitations-and-future-work.md)
- [examples.md](examples.md)
