# Suppression

`RuleSuppression` is evaluated by `RuleSuppressionService`, not by rules.

Scopes: rule ID, repository, path pattern (`fnmatch`), subject reference.
Expired suppressions do not apply. Reason and provenance are preserved.
Suppressed matches remain inspectable and are not silently deleted.
