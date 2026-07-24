# Language Evidence Providers

Phase **4.2.2** — Language Evidence Provider Foundation.

Providers collect and normalize language-aware engineering facts.
Shared Architecture Intelligence rules interpret those facts.

```
Repository
  → Language Detection
  → Language Evidence Provider Registry
  → Language-Specific Evidence Providers
  → Normalized Engineering Evidence
  → ArchitectureAnalysisView
  → Shared Architecture Rules
  → Findings and Recommendations
```

## Separation of concerns

| Layer | Responsibility |
| ----- | -------------- |
| Provider | Collects and normalizes facts |
| Architecture view | Creates language-neutral architectural meaning |
| Rule | Evaluates an assessment condition |
| Finding | Communicates an observed engineering concern |
| Recommendation | Defines a potential action |

Providers must not create Findings, assign severity, or assign business impact.

## Status

- Pipeline: **disabled by default** (`[evidence.language] enabled = false`)
- Implemented providers: Python, Java, JavaScript/TypeScript
- Reuses existing architecture extractors (no new parsers in this milestone)

## Documents

- [architecture.md](architecture.md)
- [contracts.md](contracts.md)
- [normalized-evidence.md](normalized-evidence.md)
- [capabilities.md](capabilities.md)
- [coverage.md](coverage.md)
- [provenance.md](provenance.md)
- [provider-registry.md](provider-registry.md)
- [configuration.md](configuration.md)
- [cli.md](cli.md)
- [mcp.md](mcp.md)
- [limitations.md](limitations.md)
- [adding-a-provider.md](adding-a-provider.md)
- [examples.md](examples.md)
- [python.md](python.md)
- [java.md](java.md)
- [javascript.md](javascript.md)
