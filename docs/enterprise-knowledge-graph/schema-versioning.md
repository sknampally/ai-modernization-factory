# Schema versioning

Current apiVersion: `codestrata.io/v1alpha1`

Unsupported versions are rejected. Machine-readable schemas live under
`schemas/enterprise/codestrata.io/v1alpha1/`.

Runtime validation uses typed Pydantic models and application validators; JSON
Schema supports editor integration without remote `$ref` fetching.
