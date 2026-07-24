# Positive Evidence

Reports must not contain only problems.

## Principle

**Do not infer strength merely because no negative rule matched.** Strengths
require deterministic, evidence-backed positive signals.

## Examples of positive evidence

- clear dependency direction / low cycle density
- current supported framework versions
- externalized configuration
- strong module boundaries
- comprehensive automated tests (layout + frameworks observed)
- consistent error-handling patterns
- centralized observability libraries
- stable API boundary packages

## Future record types (methodology)

When domain models are extended later, prefer explicit records such as:

- `Strength`
- `GoodPractice`
- `Capability` (observed or declared)

These are **not** implemented in Phase 4.1.2. Until then, positive evidence may
appear as narrative + evidence citations in report designs, or as findings with
informational severity only when that pattern already exists.

## Scoring interaction

Positive evidence can support `adequate` / `strong` control outcomes when
coverage is sufficient. See [scoring.md](scoring.md).
