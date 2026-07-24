# JavaScript / TypeScript Provider

- **ID:** `language.javascript.core`
- **Version:** `1.0.0`
- **Languages:** javascript (includes `.ts`/`.tsx`)
- **Consumed analyzers:** architecture ES/CJS import extractors
- **Capabilities:** source files, imports, type-only (`import type`), runtime,
  experimental units/layers, tests presence
- **Unsupported:** framework usage graph, build/workspace modules, symbols
- **Notes:** Barrel re-exports are recorded as import edges only; they are not
  treated as stronger runtime coupling beyond existing semantics.
