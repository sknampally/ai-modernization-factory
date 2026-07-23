# Security

- `yaml.safe_load` only
- no constructors, Python tags, env interpolation, or includes
- reject credential-bearing URLs and secret-like keys
- bounded file count, size, nesting, graph size, traversal depth
- no absolute paths in public errors
- no secrets in logs
