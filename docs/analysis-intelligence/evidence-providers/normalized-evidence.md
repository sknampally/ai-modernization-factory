# Normalized Evidence

Models (domain):

- `SourceUnitEvidence`
- `DependencyEvidence`
- `FrameworkUsageEvidence`
- `LanguageEvidenceBundle`
- `AggregatedLanguageEvidence`

Every item carries stable evidence ID, provider ID/version, language, provenance,
and extraction certainty fields where applicable.

Language-specific AST types do not leak into Shared Rule contracts.
