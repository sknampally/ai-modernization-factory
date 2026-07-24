# Python Provider

- **ID:** `language.python.core`
- **Version:** `1.0.0`
- **Languages:** python
- **Consumed analyzers:** `collect_raw_package_facts` / architecture extractors
- **Capabilities:** source files, imports, type-only imports, runtime deps,
  architecture units/layers, composition roots, registration, tests presence
- **Unsupported:** full symbols, framework annotations, build modules
- **Identity:** `stable_evidence_id` over provider, language, unit/dependency parts
- **Notes:** TYPE_CHECKING imports are marked type-only and excluded from
  architecture runtime edges during view finalization.
