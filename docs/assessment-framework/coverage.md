# Coverage

**Coverage** describes how much of the intended assessment area was actually
evaluated. It is separate from **confidence** (certainty of conclusions) and
**score** (quality outcome when evaluable).

## Coverage states

| State | Meaning |
| ----- | ------- |
| `complete` | Intended inputs available and analyzed |
| `substantial` | Most intended inputs analyzed; minor gaps |
| `partial` | Material gaps in languages, graphs, or configs |
| `limited` | Only thin slices assessed |
| `unavailable` | Dimension could not be assessed |

## Inputs that affect coverage

- supported languages vs repository languages
- files parsed / modules analyzed
- dependency sources loaded
- graph completeness
- build metadata availability
- configuration availability
- enterprise metadata availability
- runtime evidence availability (future)
- rule applicability rates

## Report requirements

Every dimension must show:

- assessment status (`assessed` / `not_assessed` / `insufficient_evidence`)
- coverage state (and optional percentage when defined)
- confidence
- limitations

A dimension with `limited` or `unavailable` coverage must **not** receive a
misleading Strong band.

## Example

```text
Architecture
Status: Assessed
Coverage: Substantial (82%)
Confidence: High
Limitation: Generated sources and private packages not fully resolved
```

Architecture section coverage areas use measured/partial/unsupported/not_applicable/unknown (Phase 4.2.4).
Report presentation must not render unsupported/unknown as 0% (Phase 4.2.5).
