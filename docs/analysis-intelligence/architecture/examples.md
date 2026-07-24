# Architecture Examples

## Unit selection

```text
aimf.application.rules.architecture  →  aimf.application
com.example.domain.model             →  com.example.domain
com.example.hub                      →  com.example.hub   (reverse-DNS depth ≥ 3)
```

## Cycle after collapse

Nested `aimf.ai.agents` ↔ `aimf.ai.providers` collapses into `aimf.ai` and does
not produce a self-loop finding. Cross-module cycles such as
`aimf.application` ↔ `aimf.infrastructure` remain reportable.

## Coupling

Only comparable architectural modules are scored. `aimf.cli` (composition root)
is excluded. Absolute threshold and peer-relative floor must both be met.

## Enable assess merge

```toml
[rules]
enabled = true

[rules.architecture]
enabled = true
```

```bash
aimf rules list --category architecture
aimf rules inspect architecture.dependency-cycle
aimf assess
```
