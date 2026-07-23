# Relationships

Typed relationship kinds constrain source and target entity kinds. Relationship
IDs are deterministic:

`rel:<KIND>:<source>-><target>[:discriminator]`

Declared relationships come from YAML (inline refs or `kind: Relationships`
collections). Derived relationships (assessment/finding impact) carry
`derived_*` provenance and are never inferred without a declared path.
