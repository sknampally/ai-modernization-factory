# Worked Examples

Illustrative only—no production rules are introduced by these examples.

---

## Example 1: Repository-only architecture finding

**Observed:** Package dependency cycle among core modules (derived from
Repository Graph).

| Field | Value |
| ----- | ----- |
| Taxonomy | `architecture.dependency-structure` |
| Dimension | `dimension.architecture` |
| Technical severity | High |
| Business impact | Unknown |
| Confidence | Very high |
| Coverage | Substantial |
| Evidence origin | derived (+ observed edges) |

**Executive interpretation:**  
“The application contains cyclic dependencies across core modules, increasing
the cost and risk of change.”

**Recommendation (finding-level):**  
Break the cycle by introducing a stable abstraction boundary; validate with a
follow-up graph assessment.

**Statement class:** observed/derived technical condition; inferred cost/risk
language marked as interpretation with high confidence from structural evidence.

---

## Example 2: Enterprise-enhanced technical debt

**Observed:** Unsupported framework version in dependency inventory.

**Enterprise-declared:** Application supports a strategic business capability;
five downstream applications depend on it.

| Field | Value |
| ----- | ----- |
| Taxonomy | `technical-debt.unsupported-dependencies` |
| Technical severity | Medium or high (version gap) |
| Business impact | Strategic (declared) |
| Confidence | High (version observed; criticality declared) |
| Coverage | Substantial for dependencies; enterprise context partial |

**Executive interpretation:**  
“A strategically important application depends on an unsupported framework,
creating concentrated modernization and operational risk across multiple
dependent systems.”

**Recommendation (application + portfolio):**  
Plan a Wave 2 platform upgrade initiative; coordinate downstream consumers
before cutover.

---

## Example 3: Insufficient evidence (scalability)

**Question:** Is the application scalable?

**Available evidence:** Static structure only; no runtime profile or capacity
data.

| Field | Value |
| ----- | ----- |
| Dimension | `dimension.performance-scalability` |
| Result | Not fully assessed / insufficient_evidence |
| Score | Not computed |
| Confidence | N/A for scalability conclusion |
| Coverage | Limited |

**Narrative:**  
“The repository structure was evaluated for potential scalability constraints,
but production scalability cannot be confirmed without runtime and workload
evidence.”

**Next action:** Import runtime profiles (future) or run targeted load tests;
do not assign a Strong/Weak scalability band from structure alone.
