# Provider Registry

`LanguageEvidenceProviderRegistry` supports:

- register
- get by ID
- list / list by language / list by capability
- deterministic ordering
- duplicate and version conflict rejection

Registration occurs in the composition root
(`create_language_evidence_registry`), not at import time.
