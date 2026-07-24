# Complexity Evidence (Phase 4.3.2)

Deterministic structural complexity facts for future Technical Debt rules.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Parsing / metric extraction | Language Evidence Platform |
| Debt interpretation (rules + assess) | Technical Debt Intelligence |
| Architecture Intelligence | Unchanged; does not invoke collectors |

## Configuration

```toml
[evidence.complexity]
enabled = true

[evidence.complexity.python]
enabled = true

[evidence.complexity.java]
enabled = true
```

## Support matrix

| Metric | Python | Java | JS/TS |
| ------ | ------ | ---- | ----- |
| Physical lines (file / callable / type) | yes | yes | no |
| Parameter count | yes | yes | no |
| Branch-point count | yes | yes | no |
| Max nesting depth | yes | yes | no |
| Callable count per class/module | yes | yes | no |
| Cognitive complexity | no | no | no |

## Limitations

- Java lambdas are not extracted as callables.
- Branch points are structural keyword/operator counts, not a certified
  cyclomatic-complexity product metric.
- Generated, vendor, build, and `.aimf` workspace paths are excluded by default.
- Python method/constructor parameter counts exclude implicit `self` / `cls`.
- Collectors are invoked by Technical Debt assess orchestration (4.3.4) when
  the TD pack and complexity gates are enabled; Architecture assessment does
  not register them.
