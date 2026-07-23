# Repository resolution

`RepositoryReference` manifests describe enterprise repositories. They do **not**
replace the CodeStrata repository registry.

## Resolution policy (`[enterprise]`)

- `require_registered_repositories` (default `true`)
- `allow_unresolved_repositories` (default `false`)

Unresolved references never silently create placeholder registry entries.
Ambiguous matches fail validation.

## Identity

Prefer canonical registry keys (for example `github:org/name`). Do not identify
repositories by local absolute paths. Credential-bearing URLs are rejected.

Successful resolution produces
`REPOSITORY_RESOLVES_TO_CODESTRATA_REPOSITORY` with
`resolved_repository_registry` provenance.
