# Evidence

Every matched shared rule must produce `RuleEvidence`:

- typed `kind`
- `subject_reference`
- safe message / location
- bounded attributes
- provenance
- optional line range / excerpt fingerprint (not full source)

Duplicates are removed deterministically by fingerprint. Excerpts are hashed;
large source is never persisted by the platform.
