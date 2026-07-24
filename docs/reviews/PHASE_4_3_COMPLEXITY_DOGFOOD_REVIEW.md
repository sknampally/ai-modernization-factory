# Phase 4.3.4 / 4.3.4A — Complexity Assessment Dogfood Review

**Dates:** 2026-07-24 (4.3.4), 2026-07-24 (4.3.4A precision update)  
**Milestone:** Complexity Assessment Vertical + Inventory Usability  
**Acceptance recommendation:** **Accept** (inventory usable at repository scale)

## Verdict

Phase 4.3.4 wired complexity evidence through assess. Phase **4.3.4A** makes the
raw inventory credible and usable at repository scale by:

1. Partitioning findings into **production / test / unknown** inventories
2. Driving the **primary** section inventory from **production** findings
3. Exposing test findings transparently in `finding_inventory.test`
4. Adding deterministic **source-unit hotspots** (no composite score/priority)
5. Correcting status semantics so test/fixture parse failures do **not** force
   `partially_succeeded`

CodeStrata section status is now **`succeeded`**. Primary production inventory
has **548** findings across **407** hotspots. Spring Petclinic primary inventory
is **0** production findings; **3** test findings remain visible separately.

## Finding distribution (CodeStrata)

### By rule (all roles / production)

| Rule | All | Production | Test |
| ---- | --: | ---------: | ---: |
| `technical_debt.large-callable` | 291 | 233 | 58 |
| `technical_debt.excessive-branching` | 169 | 114 | 55 |
| `technical_debt.excessive-parameters` | 111 | 97 | 14 |
| `technical_debt.oversized-type` | 126 | 87 | 39 |
| `technical_debt.deep-nesting` | 17 | 17 | 0 |
| **Total** | **714** | **548** | **166** |

### By severity / language / role

| Slice | Count |
| ----- | ----: |
| severity high (production) | 144 |
| severity medium (production) | 404 |
| language python | 714 |
| language java | 0 |
| role production | 548 |
| role test | 166 |
| role unknown | 0 |

### Unique files / symbols / overlap

| Metric | Production | Test | All |
| ------ | ---------: | ---: | --: |
| Unique files | 199 | 75 | — |
| Unique source units | 407 | 149 | — |
| Units with overlapping rules | — | — | 130 |
| Production hotspots | 407 | — | — |
| Test hotspots | — | 149 | — |

### Concentration

Top production packages by hotspot membership include
`src/aimf/application/assessment`, `src/aimf/application/incremental`,
`src/aimf/application/architecture`, and `src/aimf/interfaces/mcp`.
Overlapping rules on the same unit are common among top hotspots (up to 4 rules
on one callable), which is expected for large structural units and is now
visible via hotspot grouping rather than a flat 700-row list.

## Production / test inventory counts

| Inventory | Finding count | Notes |
| --------- | ------------: | ----- |
| Primary (`finding_ids` / `finding_summaries`) | 548 | Production only |
| `finding_inventory.production` | 548 | Same as primary |
| `finding_inventory.test` | 166 | Transparent secondary |
| `finding_inventory.unknown` | 0 | Generated/unclassified |
| `all_finding_ids` | 714 | Full traceability |
| Shared `findings.json` TD findings | 714 | Unfiltered merge |

## Deterministic hotspot inventory

Hotspots group by `(source_role, path, source_unit, language)` with:

- stable `hotspot_id` (`td-hotspot:sha256(...)`)
- finding IDs + rule IDs
- finding count
- highest observed severity
- observed metrics (metric/value/threshold/rule/finding)
- ordering: highest severity → finding count → path → source unit → id

No composite debt score or fabricated priority is introduced.

## Top 20 production hotspot review

Manual review of the top 20 production hotspots (all HIGH severity, multi-rule
where overlapping). Disposition for each: **accepted true positive** — metrics
exceed documented thresholds on real production callables; spans and parameter
counts are structural and reviewable. No threshold tuning applied.

| # | Severity | Findings | Rules | Path | Source unit | Observed metrics |
| - | -------- | -------- | ----- | ---- | ----------- | ---------------- |
| 1 | high | 4 | 4 | `src/aimf/application/architecture/conclusions/service.py` | `aimf.application.architecture.conclusions.service.ArchitectureConclusionService.build#8@71` | max_nesting_depth=5 (threshold 4); branch_point_count=34 (threshold 10); parameter_count=8 (threshold 5); physical_line_count=233 (threshold 50) |
| 2 | high | 4 | 4 | `src/aimf/application/assessment/service.py` | `aimf.application.assessment.service.AssessmentApplicationService._run_assessment_pipeline#31@457` | max_nesting_depth=6 (threshold 4); branch_point_count=84 (threshold 10); parameter_count=31 (threshold 5); physical_line_count=742 (threshold 50) |
| 3 | high | 4 | 4 | `src/aimf/application/rules/architecture/view_builder.py` | `collect_raw_package_facts#6@159` | max_nesting_depth=5 (threshold 4); branch_point_count=25 (threshold 10); parameter_count=6 (threshold 5); physical_line_count=115 (threshold 50) |
| 4 | high | 4 | 4 | `src/aimf/cli/enterprise.py` | `query_command#8@210` | max_nesting_depth=7 (threshold 4); branch_point_count=21 (threshold 10); parameter_count=8 (threshold 5); physical_line_count=84 (threshold 50) |
| 5 | high | 3 | 3 | `src/aimf/application/architecture/assessment/assembler.py` | `aimf.application.architecture.assessment.assembler.ArchitectureAssessmentAssembler.assemble#26@327` | branch_point_count=29 (threshold 10); parameter_count=26 (threshold 5); physical_line_count=223 (threshold 50) |
| 6 | high | 3 | 3 | `src/aimf/application/architecture/conclusions/clustering.py` | `cluster_findings#2@119` | max_nesting_depth=8 (threshold 4); branch_point_count=30 (threshold 10); physical_line_count=126 (threshold 50) |
| 7 | high | 3 | 3 | `src/aimf/application/assessment/service.py` | `_build_command_result#28@1701` | branch_point_count=27 (threshold 10); parameter_count=28 (threshold 5); physical_line_count=150 (threshold 50) |
| 8 | high | 3 | 3 | `src/aimf/application/assessment/service.py` | `_run_ai_assessment#14@1376` | branch_point_count=11 (threshold 10); parameter_count=14 (threshold 5); physical_line_count=150 (threshold 50) |
| 9 | high | 3 | 3 | `src/aimf/application/assessment/service.py` | `aimf.application.assessment.service.AssessmentApplicationService.run#29@197` | branch_point_count=14 (threshold 10); parameter_count=29 (threshold 5); physical_line_count=174 (threshold 50) |
| 10 | high | 3 | 3 | `src/aimf/application/enterprise/validation_service.py` | `aimf.application.enterprise.validation_service.EnterpriseManifestValidationService.validate#3@73` | max_nesting_depth=6 (threshold 4); branch_point_count=45 (threshold 10); physical_line_count=290 (threshold 50) |
| 11 | high | 3 | 3 | `src/aimf/application/incremental/impact.py` | `aimf.application.incremental.impact.ImpactAnalyzer.analyze#6@31` | branch_point_count=28 (threshold 10); parameter_count=6 (threshold 5); physical_line_count=162 (threshold 50) |
| 12 | high | 3 | 3 | `src/aimf/application/incremental/reuse.py` | `aimf.application.incremental.reuse.ReusePolicy.evaluate#9@35` | branch_point_count=51 (threshold 10); parameter_count=9 (threshold 5); physical_line_count=180 (threshold 50) |
| 13 | high | 3 | 3 | `src/aimf/application/rules/architecture/assessment.py` | `evaluate_architecture_pack_for_context_detailed#6@118` | branch_point_count=12 (threshold 10); parameter_count=6 (threshold 5); physical_line_count=121 (threshold 50) |
| 14 | high | 3 | 3 | `src/aimf/application/rules/planner.py` | `aimf.application.rules.planner.RulePlanner.plan#6@15` | branch_point_count=21 (threshold 10); parameter_count=6 (threshold 5); physical_line_count=120 (threshold 50) |
| 15 | high | 3 | 3 | `src/aimf/application/technical_debt/assessment/assembler.py` | `aimf.application.technical_debt.assessment.assembler.TechnicalDebtAssessmentAssembler.assemble#23@405` | branch_point_count=20 (threshold 10); parameter_count=23 (threshold 5); physical_line_count=167 (threshold 50) |
| 16 | high | 3 | 3 | `src/aimf/interfaces/mcp/factory.py` | `create_mcp_server#12@22` | branch_point_count=15 (threshold 10); parameter_count=12 (threshold 5); physical_line_count=117 (threshold 50) |
| 17 | high | 3 | 3 | `src/aimf/interfaces/mcp/tools/rules.py` | `register_rules_tools#2@14` | max_nesting_depth=5 (threshold 4); branch_point_count=11 (threshold 10); physical_line_count=118 (threshold 50) |
| 18 | high | 3 | 3 | `src/aimf/reporting/ai_execution.py` | `build_ai_execution_document#15@65` | branch_point_count=44 (threshold 10); parameter_count=15 (threshold 5); physical_line_count=170 (threshold 50) |
| 19 | high | 3 | 3 | `src/aimf/static_analysis/providers/pmd_discovery.py` | `resolve_pmd_executable#8@38` | branch_point_count=27 (threshold 10); parameter_count=8 (threshold 5); physical_line_count=90 (threshold 50) |
| 20 | high | 2 | 2 | `src/aimf/ai/providers/bedrock.py` | `aimf.ai.providers.bedrock.BedrockAIModelProvider.invoke#2@74` | branch_point_count=18 (threshold 10); physical_line_count=102 (threshold 50) |

Notable concentration: `AssessmentApplicationService` methods dominate (large
orchestration callables). This is credible structural debt signal, not
contamination.

## `partially_succeeded` explanation and correction

### Previous (4.3.4) behavior

Status became `partially_succeeded` whenever `files_failed > 0`. CodeStrata had
exactly one failed file:

`tests/.../fixtures/python/unsupported_syntax.py`

That fixture is **intentionally unparseable** and classified **test**. Treating
it as a provider execution failure incorrectly degraded repository-scale status.

Unsupported languages (JS/TS) and unavailable optional metrics (cognitive
complexity) were never counted as failures; they remain limitations only.

### Corrected (4.3.4A) semantics

- Record all parse failures in diagnostics and `files_parse_failed`
- Count **production** parse failures as `provider_failures` / material
- Test/fixture/generated parse failures do **not** force `partially_succeeded`
- Emit diagnostics:
  - `non_material_parse_failures_do_not_degrade_status:N`
  - `parse_failures_total_vs_production:total:production`

### Current CodeStrata result

| Field | Value |
| ----- | ----- |
| status | **`succeeded`** |
| files_parse_failed | 1 |
| production_parse_failures | 0 |
| provider_failures | 0 |

## Contamination verification (primary production inventory)

| Content class | In primary inventory? |
| ------------- | --------------------- |
| `.aimf/` workspace | **0** |
| fixtures | **0** |
| vendor | **0** |
| generated | **0** |
| JS/TS | **0** (unsupported; not collected) |

## Spring Petclinic source-role verification

| Check | Result |
| ----- | ------ |
| `src/main/java` classification | production (`SourceClassification.SOURCE`) |
| `src/test/java` classification | test |
| Complexity files measured | **49 / 49** (`complexity_coverage` measured) |
| Production evidence collected | **Yes** (coverage numerator/denominator) |
| Primary production findings | **0** |
| Test findings (transparent) | **3** |
| Section status | `succeeded` |

Only genuinely qualifying **test** units emitted findings:

| Path | Source unit | Rule | Metric | Value | Threshold | Role |
| ---- | ----------- | ---- | ------ | ----- | --------- | ---- |
| `src/test/java/org/springframework/samples/petclinic/PetClinicConcurrencyTests.java` | `PetClinicConcurrencyTests.testDuplicatePetNameRaceConditionIsBlocked#0@40` | `technical_debt.large-callable` | physical_line_count | 93 | 50 | test |
| `src/test/java/org/springframework/samples/petclinic/system/I18nPropertiesSyncTest.java` | `I18nPropertiesSyncTest.checkI18nPropertyFilesAreInSync#0@86` | `technical_debt.large-callable` | physical_line_count | 51 | 50 | test |
| `src/test/java/org/springframework/samples/petclinic/system/I18nPropertiesSyncTest.java` | `I18nPropertiesSyncTest.checkNonInternationalizedStrings#0@39` | `technical_debt.excessive-branching` | branch_point_count | 13 | 10 | test |

Manual disposition: all three are threshold-faithful structural signals on test
sources; correctly excluded from the primary production inventory.

## Repeated-run stability (CodeStrata)

Two consecutive enabled assess runs produced **byte-identical**
`technical-debt-assessment.json` artifacts (status, inventories, hotspot IDs,
finding IDs).

## Credibility assessment

| Dimension | Rating | Notes |
| --------- | ------ | ----- |
| Inventory usability | **High** | Production-primary + hotspots |
| Role separation | **High** | Petclinic proves production empty / test visible |
| Status semantics | **High** | Fixture parse failure no longer degrades status |
| Determinism | **High** | Identical repeat artifacts |
| Narrative volume | Medium | 548 production findings still large, but hotspots make review tractable |
| Overall | **High** | Accept for 4.3.4A |

## Explicit acceptance decision

**Accept Phase 4.3.4A.** The complexity inventory is credible and usable at
repository scale for production-first review. Proceed to later milestones
(conclusions / report) without requiring threshold suppression.

## Known limitations (unchanged / deferred)

- No conclusions, recommendations, scoring, or prioritization formulas
- No financial / effort / velocity / business-impact claims
- No CTO report JSON/HTML debt section
- No duplication or smell rules
- No JS/TS or cognitive complexity
- Nested Python callables not extracted independently (outer span may include nested bodies)
- Branch points are structural counts, not certified cyclomatic products
- Test findings remain measured and exposed (not suppressed)

## Artifacts

- CodeStrata: `reports/dogfood-phase-4-3-4A/codestrata/.../technical-debt-assessment.json`
- Petclinic: `reports/dogfood-phase-4-3-4A/petclinic/.../technical-debt-assessment.json`
