# Provider Contract

`LanguageEvidenceProvider` protocol:

- `metadata` → `LanguageEvidenceProviderMetadata`
- `evaluate_applicability(context)` → `ProviderApplicability`
- `collect(context)` → `LanguageEvidenceCollectionResult`
- `explain_applicability(context)` → structured dict

Applicability statuses: `applicable`, `not_applicable`, `insufficient_input`.

Execution statuses: `succeeded`, `partially_succeeded`, `failed`,
`not_applicable`, `insufficient_input`.

Expected applicability conditions are returned as structured results, not raised
as exceptions. Unexpected failures are isolated by the executor.
