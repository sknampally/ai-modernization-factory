# Severity, Business Impact, and Priority

These three concepts must remain separate.

| Concept | Question |
| ------- | -------- |
| **Technical severity** | How serious is the engineering condition? |
| **Business impact** | How consequential could this be to the organization? |
| **Priority** | How soon should the organization act? |

## Technical severity

Aligns with existing Phase 3 `FindingSeverity`:

| Level | Meaning | Likely consequence | Urgency | Remediation expectation |
| ----- | ------- | ------------------ | ------- | ----------------------- |
| `informational` | Notable fact; little risk | Awareness | None | Optional hygiene |
| `low` | Minor engineering concern | Limited local friction | Low | Backlog |
| `medium` | Meaningful maintainability or risk | Elevated change cost / risk | Moderate | Planned work |
| `high` | Serious engineering risk | Significant failure or cost modes | High | Near-term remediation |
| `critical` | Severe condition | Systemic risk or exposure | Immediate validation/action | Stabilize first |

**Examples**

- informational: detected Node engine constraint documented
- low: oversized module
- medium: missing automated tests on a non-trivial codebase
- high: cyclic core dependencies; unsupported major framework
- critical: plaintext secrets committed; actively unsupported platform with known RCE class risk when verified via imported advisories

Technical severity is **not** automatically derived from business criticality.

## Business impact

| Level | Meaning |
| ----- | ------- |
| `unknown` | Default for repository-only assessment |
| `limited` | Localized / non-critical systems |
| `moderate` | Material operational or capability effect |
| `high` | Broad user/operational consequence |
| `strategic` | Core capability, regulatory, or portfolio-critical |

### Inputs (when available)

- application criticality (enterprise-declared)
- business capability importance
- user reach / revenue relevance (declared only)
- regulatory relevance (declared)
- operational dependency / downstream count
- replacement difficulty
- modernization initiative relevance

### Rules

- Repository-only assessments normally use `unknown` or explicitly **bounded
  inferred** impact with low confidence.
- Do **not** fabricate business impact without enterprise context or user-supplied
  metadata.
- Enterprise-declared criticality must be labeled as declared, not observed.

## Risk

**Risk** combines potential consequence, exposure, and uncertainty. It is a
narrative and prioritization aid—not a single opaque number.

Low-confidence critical findings may require **validation** before remediation
commitment.

## Priority bands

| Band | Meaning |
| ---- | ------- |
| `immediate` | Validate/stabilize now |
| `near_term` | Schedule soon |
| `planned` | Include in a defined initiative |
| `monitor` | Watch; no urgent change |
| `informational` | Awareness only |

### Priority may consider

- technical severity
- business impact
- confidence
- scope / blast radius
- dependency centrality
- remediation effort band
- modernization dependencies
- time sensitivity
- strategic alignment (declared)

Do not collapse severity + impact + confidence into one hidden score.
