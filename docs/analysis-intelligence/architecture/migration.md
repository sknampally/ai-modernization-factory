# Architecture Pack Migration / Compatibility

- Legacy `RuleEngine` / `aimf-rule-*` findings unchanged when pack disabled
- Shared Rule Platform remains the only execution path for new architecture rules
- No third rule engine
- Finding IDs for legacy rules unchanged
- Reports remain renderable; architecture findings enter the same findings artifact
- Enterprise Knowledge Graph remains optional
- Package name stays `aimf`; CLI stays `aimf` (rebrand deferred)

## Incremental invalidation

Safe full pack reevaluation after relevant changes. Invalidation dependencies:

| Rules | Invalidate when |
| ----- | --------------- |
| Cycles / coupling / concentration | dependency edges, source imports, graph fingerprint |
| Layer / boundary / leakage | edges, layer markers, architecture configuration |
| Enterprise mismatch | enterprise standard version / context |

Deterministic ordering preserved via sorted rule IDs and match sort keys.
