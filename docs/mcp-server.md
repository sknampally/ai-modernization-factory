# CodeStrata MCP server

**Status:** Phase 2C (FastMCP adapter).

CodeStrata exposes durable modernization knowledge and assessment execution to
MCP clients through a thin FastMCP adapter.

## Architecture

```text
MCP client (Cursor, etc.)
        ↓
aimf mcp serve  (stdio)
        ↓
CodeStrata FastMCP tools / resources / prompts
        ↓
KnowledgeQueryService / AssessmentApplicationService
        ↓
KnowledgeStore ports → SQLite + verified blobs
```

MCP never executes SQL, opens blob files, or reads `report.json` / `report.html`.

Sibling adapters (CLI, future REST, future Agent Framework) call the same
application services. Agents must **not** call the MCP server internally.

## Dependency

Official MCP Python SDK:

```text
mcp>=1.27,<2
```

FastMCP API: `mcp.server.fastmcp.FastMCP`.

## Start the server

```bash
aimf mcp serve --config aimf.toml
```

Transport: **stdio** only in this phase.

Logs go to **stderr** so MCP protocol traffic on stdout stays clean.

Optional config (all fields optional; existing `aimf.toml` files remain valid):

```toml
[mcp]
enabled = true
transport = "stdio"
log_level = "INFO"
```

## Example Cursor MCP config

```json
{
  "mcpServers": {
    "codestrata": {
      "command": "/path/to/ai-modernization-factory/.venv/bin/aimf",
      "args": ["mcp", "serve", "--config", "/path/to/project/aimf.toml"]
    }
  }
}
```

Do not embed credentials in MCP configuration.

## Tools

| Tool | Purpose |
| ---- | ------- |
| `list_repositories` / `get_repository` | Repository discovery |
| `list_assessments` / `get_assessment` / `get_latest_assessment` | Assessment history |
| `list_snapshots` / `get_snapshot` / `compare_snapshots` | Snapshot history + diff |
| `list_findings` / `get_finding` / `explain_finding` | Phase 3 findings |
| `list_recommendations` / `get_recommendation` / `explain_recommendation` | Phase 3 recommendations |
| `list_components` / `get_component` / `get_component_dependencies` | Graph components |
| `get_ai_execution` / `get_ai_enrichment` | Optional AI artifacts |
| `run_assessment` | Execute assessment + persist knowledge |

## Resources

- `codestrata://repositories`
- `codestrata://repositories/{repository_id}`
- `codestrata://repositories/{repository_id}/latest-assessment`
- `codestrata://assessments/{run_id}/findings`
- `codestrata://assessments/{run_id}/recommendations`

## Prompts

- `review_repository`
- `explain_modernization_plan`
- `review_snapshot_changes`

Prompts supply deterministic JSON context; the client model interprets. They do
not call Bedrock inside the MCP server.

## Limits

Collection tools return `{items, returned_count, truncated, limit}`.

Defaults/maxima match KnowledgeQueryService bounds (repositories 50/500,
assessments 20/200, findings 100/500, components 100/1000, dependency depth ≤ 3).

Full graphs, manifests, and HTML reports are not returned by general tools.

## Security / trust model

This server is a **local developer tool**.

- No authentication
- Not safe for untrusted public network exposure
- No arbitrary filesystem/SQL/shell tools
- Local path aliases omitted from public repository DTOs
- Credential-bearing URLs rejected by existing validators
- Errors sanitized (no stack traces, secrets, or sqlite details)

## Assessment execution

`run_assessment` calls `AssessmentApplicationService`, persists knowledge through
the existing store, and returns concise IDs + counts for follow-up query tools.

## Next Phase 2 step

Thin optional CLI / MCP adapters over the Phase 2D Agent Framework (already
implemented under `aimf.application.agents`). See
[agent-framework.md](agent-framework.md).
