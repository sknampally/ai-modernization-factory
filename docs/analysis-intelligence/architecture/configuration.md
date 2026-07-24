# Architecture Configuration

Disabled by default. Existing configs without `[rules]` remain valid.

```toml
[rules]
enabled = false

[rules.architecture]
enabled = false

[rules.architecture.unit_selection]
module_depth = 2
composition_root_markers = ["cli", "main", "bootstrap", "boot", "entrypoint", "wiring"]
registration_markers = ["registry", "registration", "di", "plugin", "factory"]
ignore_path_markers = ["/generated/", "/.generated/", "/vendor/"]

[rules.architecture.dependency_cycle]
enabled = true

[rules.architecture.invalid_dependency_direction]
enabled = true

[rules.architecture.layer_boundary_violation]
enabled = true

[rules.architecture.excessive_cross_module_coupling]
enabled = true
outgoing_module_threshold = 8
minimum_module_count = 5
relative_multiplier = 2.0
exclude_composition_roots = true

[rules.architecture.component_concentration]
enabled = true
incident_edge_share_threshold = 0.30
minimum_component_count = 5

[rules.architecture.framework_leakage]
enabled = true

[rules.architecture.service_dependency_cycle]
enabled = true
# Deferred: toggle only

[rules.architecture.enterprise_standard_mismatch]
enabled = true
```

## Notes

- Cycle detection does not require architecture declarations when the import graph is available.
- Layer / boundary rules are conservative without reliable classification coverage.
- Coupling requires **both** absolute and peer-relative thresholds.
- Assess executes the pack only when `rules.enabled` and `rules.architecture.enabled` are true.
