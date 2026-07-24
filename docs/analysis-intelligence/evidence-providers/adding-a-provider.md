# Adding a Provider

1. Detect language/ecosystem.
2. Extract evidence via existing analyzers where possible.
3. Normalize to domain evidence models.
4. Register in `create_language_evidence_registry`.
5. Declare capabilities, maturity, and limitations.
6. Add tests and provider documentation.
7. Reuse shared Architecture Intelligence rules.

Do not add language-only architecture rule packs unless a concept is genuinely
unique.
