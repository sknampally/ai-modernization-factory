# Enterprise querying

`EnterpriseKnowledgeQueryService` answers typed, bounded questions. It does not
expose Cypher, SQL, or unrestricted traversal.

## Graph layers

| Graph | Scope |
|-------|--------|
| Repository Graph | Files/modules inside one repo |
| Engineering Knowledge Graph | Technology concepts from assessment |
| Assessment Graph | Findings/recommendations for a run |
| Enterprise Knowledge Graph | Cross-repo enterprise architecture |

`KnowledgeQueryService` remains the repository knowledge API.
`EnterpriseKnowledgeQueryService` is enterprise-level.
`EnterpriseContextQueryService` composes the two without circular deps.

## Supported query shapes

- Entity by ID / list by kind
- Applications by domain or capability
- Repositories and services by application
- Ownership chains (team → application/service/repository)
- Service dependencies and data-store consumers
- Standards applicability
- Repository enterprise context
- Finding / recommendation enterprise impact
- Bounded dependency paths and neighborhoods

## Limits

Configured under `[enterprise]`:

- `max_query_results`
- `max_traversal_depth` (hard ceiling 10)
- `max_dependency_paths`

Results are deterministic and cycle-safe. Truncation is reported when applicable.

## CLI / MCP

See [cli.md](cli.md) and [mcp.md](mcp.md). Prefer high-level operations such as
`aimf enterprise query impact --repository student-api` over raw graph dumps.
