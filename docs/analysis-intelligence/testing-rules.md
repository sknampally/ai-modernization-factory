# Testing rules

```python
from aimf.application.rules.testing import RuleTestHarness
from aimf.domain.rules.enums import RuleResultStatus

harness = RuleTestHarness([MyRule()])
result = harness.execute_one(MyRule())
harness.assert_status("my.category.rule-id", result, RuleResultStatus.MATCHED)
harness.assert_match_count(result, 1)
findings = harness.map_findings(result)
```

Internal fixtures (`fixture.always-match`, …) live in
`aimf.application.rules.fixtures` and must be registered with
`production=False`.
