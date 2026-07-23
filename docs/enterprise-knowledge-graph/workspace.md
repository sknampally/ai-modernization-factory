# Enterprise YAML workspace

Default location: `enterprise/`

Recommended layout:

- one entity per file under typed directories
- collection files under `relationships/` for explicit edges
- root `enterprise.yaml` for workspace policy only

Supported extensions: `.yaml`, `.yml`

Loading is recursive within the workspace, deterministic by relative path, and
rejects symlink escape, oversized files, excessive nesting, and unsafe YAML tags.
