# Scoring Methodology

**Status:** Provisional methodology. Not wired into `aimf assess` or the current
HTML Engineering Assessment (which intentionally avoids composite “health”
scores today—see `docs/report-generation.md`).

## Anti-patterns

Avoid:

```text
score = 100 - arbitrary_penalties
```

Avoid averages that hide critical findings.

## Defensible approach

1. Evaluate **controls / assessment areas** (taxonomy nodes).
2. Classify each as: `strong` | `adequate` | `needs_attention` | `weak` |
   `critical` | `not_assessed` | `insufficient_evidence`.
3. Compute a numeric score **only when minimum coverage is met**.
4. Attach **confidence** and **coverage** to every score.
5. Surface **material findings** separately from the headline band.
6. Allow critical findings to **cap or qualify** the headline result.
7. Preserve a full **score explanation**.

## Provisional score bands

Label as provisional—not scientific precision:

| Score | Band |
| ----- | ---- |
| 85–100 | Strong |
| 70–84 | Generally Sound |
| 50–69 | Needs Attention |
| 30–49 | Weak |
| 0–29 | Critical Concern |

Preferred display:

```text
Needs Attention
Score: 67
Confidence: High
Coverage: 82%
```

Internal integers (e.g., 67) are acceptable; reports should lead with the band.

## Score explanation (required fields)

Every score must answer:

- why it received the score
- what evidence / findings contributed
- what was not assessed
- what could materially change the score
- what actions would improve it

Conceptual shape:

```text
ScoreExplanation
  dimension_id
  band
  score (optional int)
  confidence
  coverage
  control_outcomes[]
  contributing_finding_ids[]
  positive_evidence_ids[] (when available)
  material_overrides[]   # e.g., critical finding caps band
  limitations[]
  not_assessed_areas[]
```

## Material overrides

Examples:

- Any `critical` technical finding with confidence ≥ high → headline band cannot
  exceed **Needs Attention** without an explicit override rationale.
- Multiple `high` findings in a core module → cap at **Needs Attention** or
  **Weak** depending on coverage.

Overrides are documented, deterministic policies—not silent score edits.

## Dimension and subdimension scores

- Subdimension scores roll into dimension scores only with documented weights or
  equal contribution plus override rules.
- Cross-dimension aggregation (overall engineering health) is optional and must
  restate coverage/confidence; never a single fake-precision number alone.

## Positive evidence

Strengths may raise outcomes toward `adequate`/`strong` only when **positive
evidence** exists—not merely because no negative rule matched.

## Implementation note

No production scoring code is introduced in Phase 4.1.2. Future implementation
must reuse Shared Rule Platform findings and preserve existing finding IDs.
