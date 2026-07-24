# Examples

Plan providers for a repository:

```bash
aimf evidence plan --repository . --json
```

Inspect Python provider metadata:

```bash
aimf evidence providers inspect language.python.core --json
```

Enable the pipeline only when intentionally validating equivalence:

```toml
[evidence.language]
enabled = true
```
