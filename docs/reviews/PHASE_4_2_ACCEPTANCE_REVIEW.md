# Phase 4.2 Architecture Intelligence — Acceptance Review

**Date:** 2026-07-24  
**Scope:** End-to-end review of Architecture Intelligence (4.2.1–4.2.5)  
**Decision:** **C — PRECISION CORRECTION REQUIRED**  
**Commit readiness:** Not ready to commit Phase 4.2 as accepted  
**Production code changed during this review:** No

---

## Executive decision

Phase 4.2’s pipeline (evidence → rules → findings → conclusions → assessment →
report) is wired and largely well-bounded. The **core CodeStrata Option A
signals remain credible**. However, the latest dogfood **7/6/6** result is not
an acceptable representation of CodeStrata architecture because it includes:

1. **Three framework-leakage findings** sourced from
   `.aimf/workspace/spring-petclinic` (workspace contamination).
2. **One coupling finding on `tests`**, which is misclassified as an application
   architectural module.
3. **Conclusion/recommendation fragmentation** (three near-identical framework
   conclusions and recommendation groups).

These are analytical/applicability defects (scanner exclusion + unit role/layer
selection + clustering granularity), not report-adapter defects. Report
integration faithfully presents the assessment section.

---

## Inputs reviewed

| Artifact | Used |
| -------- | ---- |
| `reports/architecture-report-4.2.5/.../20260724-050133/report.json` | Yes |
| `.../report.html` | Yes |
| `.../architecture-assessment.json` | Yes |
| `.../architecture_conclusions.json` | Yes |
| `.../findings.json` | Yes |
| `reports/architecture-report-self-assessment-4.2.5.txt` | Yes |
| `reports/architecture-assessment-self-assessment-4.2.4.txt` | Yes |
| `reports/architecture-assessment-4.2.4/architecture-assessment.json` | Yes |
| `reports/architecture-conclusions-self-assessment-4.2.3.txt` | Yes |
| `reports/architecture-self-assessment-4.2.1a.txt` | Yes |
| Dogfood configs under `reports/architecture-report-4.2.5/` and acceptance repro | Yes |
| Vinay reference report | **Not available** in workspace |

Reference report comparison was **not performed** because Vinay’s report was
not available in the current workspace.

---

## Part 1 — Explain 3/2/2 → 7/6/6

### Summary reason

The increase is **not** caused by the report adapter, schema changes, stale
artifact loading, or conclusion-policy rewrites for presentation.

It is caused by **expanded architecture-analysis input population** when
assessing repository `path = "."` while `.aimf/workspace/spring-petclinic`
remains on disk, combined with **test-unit coupling eligibility**.

Critical evidence:

- `LocalRepositoryScanner.DEFAULT_EXCLUDED_DIRECTORIES` does **not** include
  `.aimf`.
- A local scan of `.` currently includes **~1173 paths under `.aimf/`** and
  exposes primary units such as
  `org.springframework.samples.petclinic.model`.
- Reproducing assess with `[evidence.language] enabled = false` still yields
  **7 findings / 6 conclusions / 6 recommendation groups** under
  `evidence_pipeline: legacy_view_builder`.
- The original three finding IDs from 4.2.3/4.2.4 remain **byte-identical**.

### Comparison table

| Item | Earlier (4.2.3/4.2.4) | Current (4.2.5 dogfood) | Reason for change | Expected or defect | Evidence |
| ---- | -------------------- | ----------------------- | ----------------- | ------------------ | -------- |
| Visible findings | 3 | 7 | +1 coupling on `tests`; +3 framework leakage on petclinic workspace | Defect (contamination + test applicability) | Finding ID diff; scopes |
| Conclusions | 2 | 6 | +1 coupling conclusion; +3 framework conclusions (1:1 with findings) | Defect / fragmentation | Policy telemetry `produced_2`, `produced_3` |
| Recommendation groups | 2 | 6 | One group per conclusion | Follows conclusion fragmentation | Assessment artifact |
| Extraction coverage | 1.0 | 1.0 | Unchanged | Expected | Coverage areas |
| Classification coverage | 0.3125 | 0.2857 | More primary units (incl. petclinic/tests) dilute classified share | Defect side-effect | Coverage ratios |
| Evidence pipeline label | `legacy_view_builder` | `language_evidence` (4.2.5 dogfood) / still 7/6/6 with language off | Config difference; **not** root cause of count jump | Environmental / config | Repro run `legacy-like` |
| Core finding IDs | 3 stable IDs | Same 3 preserved | Deterministic ID stability for unchanged subjects | Expected | ID set intersection |
| Boundary conclusion ID | `...:2ef46a46...` | `...:bb866f38...` | Conclusion ID hash changed despite identical source finding IDs | Soft defect (stability) | Side-by-side ID compare |
| Report section | absent | present | 4.2.5 adapter | Expected | `assessment.architecture` |

### New findings (detail)

| Finding ID | Rule | Scope | Credible for CodeStrata? | Notes |
| ---------- | ---- | ----- | ------------------------ | ----- |
| `...dependency-cycle:5beba100...` | dependency-cycle | `aimf.application` ↔ `aimf.infrastructure` | Yes | Stable since 4.2.1a |
| `...invalid-dependency-direction:ed578f0e...` | invalid-direction | application → infrastructure | Yes | Stable |
| `...excessive-cross-module-coupling:e304410e...` | coupling | `aimf.application` (`out:10`) | Yes | Stable Option A |
| `...excessive-cross-module-coupling:03c987be...` | coupling | `tests` (`out:15`) | No / weak | `tests` layer classified as `application`; enters coupling peers |
| `...framework-leakage:186c0b1b...` | framework-leakage | petclinic `Person.java` / JPA | No | Workspace contamination |
| `...framework-leakage:37b35be9...` | framework-leakage | petclinic `NamedEntity.java` | No | Workspace contamination |
| `...framework-leakage:d038540d...` | framework-leakage | petclinic `BaseEntity.java` | No | Workspace contamination |

---

## Part 2 — Finding-by-finding review

| Finding | Verdict | Credibility | Distinctness | Severity OK | Confidence OK | Action |
| ------- | ------- | ----------- | ------------ | ----------- | ------------- | ------ |
| dependency-cycle `5beba100` | **Accept** | High | Distinct boundary signal | Yes (medium) | Yes (high) | Keep |
| invalid-direction `ed578f0e` | **Accept** | High | Related to cycle; correctly co-concluded | Yes | Yes (medium) | Keep |
| coupling `e304410e` (`aimf.application`) | **Accept** | High | Distinct from boundary | Yes | Yes | Keep |
| coupling `03c987be` (`tests`) | **Needs precision correction** | Low for product architecture | Distinct subject, wrong population | Severity OK if applicable | Overstated confidence for test tree | Exclude test units from coupling peers / fix layer |
| framework-leakage `186c0b1b` | **False positive** (for this repo assess) | High as JPA-in-model observation; **low** as CodeStrata concern | Overlaps sibling leakages | Medium OK for real domain leakage | High too strong for contaminated input | Exclude `.aimf` from scan/view |
| framework-leakage `37b35be9` | **False positive** | Same | Duplicate theme | Same | Same | Same |
| framework-leakage `d038540d` | **False positive** | Same | Duplicate theme | Same | Same | Same |

### Notes on false-positive classification

The framework-leakage rule behaves correctly **given** that
`org.springframework.samples.petclinic.model` is treated as an in-repo domain
unit. The defect is **upstream input selection**: assessing CodeStrata should
not ingest `.aimf/workspace` clones.

---

## Part 3 — Conclusion review

| Conclusion | Source findings | Verdict | Executive usefulness | Overlap | Action |
| ---------- | --------------- | ------- | -------------------- | ------- | ------ |
| boundary-integrity `bb866f38` | cycle + invalid-direction | **Accept** | High | None material | Keep (ID churn soft issue) |
| broad-dependency `e05899c6` (`aimf.application`) | coupling `e304410e` | **Accept** | Medium-High | None | Keep |
| broad-dependency `7a47a449` (`tests`) | coupling `03c987be` | **Too weak** / needs correction | Low | Title duplicates sibling | Remove via finding fix |
| framework-erosion ×3 | one leakage each | **Duplicate** / fragmentation | Low as three cards | High overlap | Cluster by package/unit; or disappear after `.aimf` exclusion |

Executive-summary dedupe of titles helps, but HTML still shows three repeated
conclusion cards and six recommendation cards.

Materiality (`notable` for boundary; `contextual` for others) and business
impact (`unknown`) are appropriate. No unsupported business language found.

---

## Part 4 — Recommendation review

| Group | Specific? | Addresses source? | Duplicate? | Actionable? | Avoids cost/staffing? | Wave 2 OK? | Verdict |
| ----- | --------- | ----------------- | ---------- | ----------- | --------------------- | ---------- | ------- |
| boundary `53a0a8c6` | Yes | Yes | No | Yes | Yes | Yes | **Accept** |
| coupling application `689aee54` | Moderately generic | Yes | No | Yes | Yes | Yes | **Accept** |
| coupling tests `2f6e0e6a` | Generic | Source is weak | Theme dup | Misleading | Yes | Questionable | **Needs correction** (follow finding) |
| framework ×3 | Same text thrice | Per-file yes | **Yes** | Yes for real leakage | Yes | Yes if in-scope | **Merge presentation / remove via exclusion** |

Report should, after precision correction, show the two Option A groups
prominently. Visual grouping of related groups is optional and non-blocking.

Do **not** alter recommendation IDs for presentation reasons.

---

## Part 5 — Coverage and limitations

| Question | Answer |
| -------- | ------ |
| Is 28.6% classification prominent enough? | Partially — shown in metrics + coverage table + executive summary. Could be stronger as a callout near conclusions. |
| Could a CTO assume full classification? | Unlikely if they read coverage; possible if they only skim conclusion cards. |
| Are conclusions bounded by partial classification? | Boundary confidence medium; limitations include partial-classification. Contaminated findings are the larger issue. |
| Confidence capped correctly? | Mostly; framework leakage confidence `high` is too strong for workspace-sourced hits. |
| Unsupported shown as unsupported (not 0%)? | Yes |
| Limitations understandable? | Yes |
| Business impact clearly unknown? | Yes |
| Overstates certainty? | Medium risk due to contaminated findings presented as repository architecture |

Presentation-only improvements are secondary to precision correction.

---

## Part 6 — CTO credibility ratings

| Dimension | Rating | Evidence |
| --------- | ------ | -------- |
| Credibility | **Medium → Low** on current dogfood; **High** for core Option A alone | Petclinic/tests findings dominate narrative |
| Executive readability | **Medium** | Summary is clear; repeated conclusion cards hurt |
| Technical traceability | **High** | Stable IDs across assessment/report; sample edges |
| Evidence transparency | **Medium** | Paths reveal workspace contamination rather than hiding it |
| Actionability | **Medium** | Boundary + application coupling actionable; framework/tests noisy |
| Overstatement risk | **Medium** | Medium severity retained, but irrelevant findings inflate concern count |

Would a CTO trust the report enough for follow-ups? **Yes for Option A
topics; no for the full 7/6/6 narrative** until workspace contamination is fixed.

---

## Part 7 — Reference report comparison

**Reference report comparison not performed because the report was not available
in the current workspace.**

---

## Part 8 — End-to-end integrity

| Check | Result |
| ----- | ------ |
| Finding IDs stable for unchanged subjects | Pass (3 core IDs unchanged) |
| Recommendation/conclusion IDs unchanged globally | Fail soft — conclusion IDs for same sources changed; new IDs for new findings |
| Report references correct IDs | Pass |
| No duplicate analysis in adapter | Pass (adapter-only) |
| No stale artifact loading in assess path | Pass (in-memory section) |
| One assessment + one report architecture section | Pass |
| Traceability links resolve | Pass |
| Suppressed findings excluded | Pass (none suppressed) |
| No raw source code in report | Pass |
| No absolute `/Users/` paths | Pass |
| Workspace-relative `.aimf/workspace/...` paths present | Fail product intent (contamination visible) |
| No inferred business impact | Pass |
| No AI narrative | Pass |
| No score/grade in architecture section | Pass |
| Disabled behavior unchanged | Pass (defaults remain false; unit tests) |
| Old report.json readable (schema 1.2) | Pass |
| Deterministic adapter regeneration | Pass |

---

## Part 9 — Acceptance decision

### Decision: **C. PRECISION CORRECTION REQUIRED**

### Rationale

Report integration is credible and bounded, and the core architecture signals
remain sound. Acceptance of Phase 4.2 as a whole is blocked by confirmed
input-selection / applicability defects that produce non-credible findings in
the CodeStrata dogfood report.

### Blocking issues

1. **`.aimf` workspace contamination** in repository scan / architecture file
   collection → false framework-leakage findings from spring-petclinic.
2. **`tests` treated as coupling-comparable architectural module** (layer
   misclassification / missing test-role exclusion).

### Non-blocking issues

- Conclusion ID instability for identical source finding sets when graph
  fingerprint changes.
- Framework conclusions not clustered by package (fragmentation) — becomes moot
  if contamination is fixed; still worth tightening later.
- Executive/HTML repetition of identical titles.
- Classification-coverage callout could be stronger near conclusions.
- Provider telemetry (`providers_planned: 0` while pipeline label may say
  `language_evidence`) is inconsistent/confusing.
- Dual rule engines and aimf/CodeStrata naming debt remain.

### Required corrections (narrow)

1. **Scanner / architecture path exclusion:** default-exclude `.aimf` (and
   preferably report/knowledge workspace dirs) from repository file population
   used by architecture analysis.
2. **Coupling applicability:** exclude units with test identity (unit token /
   layer / role) from `comparable_coupling_units` consistently.
3. Re-dogfood CodeStrata and confirm return to Option A shape (≈3/2/2) **without
   changing thresholds to force the count**.

### Optional improvements

- Cluster framework-leakage conclusions by primary domain unit.
- Report presentation: group duplicate-titled conclusions visually.
- Strengthen classification-coverage callout adjacent to conclusions.
- Stabilize conclusion IDs to source findings + policy (exclude volatile
  fingerprints if present).

### What must not change

- Core finding severities/confidence for Option A findings
- Rule thresholds solely to reduce counts
- Scoring / AI narrative
- Package/CLI rename
- Recommendation text mutation for cosmetics
- Canonical finding IDs for unchanged subjects

### Can Phase 4.2 be committed now?

**No — not as an accepted Phase 4.2 milestone.**  
Implementation may remain on the branch, but acceptance and “complete” roadmap
status should wait for the precision correction above.

---

## Confirmed defects (do not implement in this review)

| Defect | Smallest responsible component | Proposed correction |
| ------ | ------------------------------ | ------------------- |
| Workspace clone treated as product source | `LocalRepositoryScanner` (+ architecture ignore markers) | Exclude `.aimf` by default |
| `tests` coupling finding | `classify_layer` / `comparable_coupling_units` / role classification | Treat `tests` as test layer/role and exclude from coupling peers |
| Conclusion ID churn with identical sources | conclusion identifier hashing inputs | Hash stable identity fields only |
| Framework conclusion 1:1 fragmentation | conclusion clustering policy | Optional cluster-by-unit for framework leakage |

---

## Validation performed during review

- Inspected 4.2.3/4.2.4/4.2.5 self-assessments and artifacts
- Compared finding/conclusion/recommendation IDs
- Reproduced assess with language evidence disabled → still 7/6/6
- Confirmed scanner includes `.aimf` paths
- Confirmed adapter deterministic regeneration and report ID integrity
- Confirmed no `/Users/` absolute paths in architecture report payload
- Confirmed Vinay reference report unavailable
