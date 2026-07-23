# CLI

```bash
aimf enterprise init [dir] [--examples] [--minimal] [--force]
aimf enterprise validate [dir] [--json] [--strict]
aimf enterprise build [dir] [--json]
aimf enterprise inspect [entity-id] [--depth N] [--json]
aimf enterprise query applications|repositories|impact|ownership|dependencies ...
aimf enterprise explain <relationship-id>
aimf enterprise compare <left-graph-id> <right-graph-id>
```

Thin adapters only; workflow lives in `EnterpriseKnowledgeService`.
