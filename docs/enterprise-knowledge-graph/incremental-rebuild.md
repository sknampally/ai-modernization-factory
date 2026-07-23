# Incremental enterprise graph rebuild

Phase 3 rebuilds the complete Enterprise Knowledge Graph after workspace
validation. Interfaces fingerprint manifests and support future selective
rebuild, but the implementation always falls back to a full rebuild rather than
claiming partial reuse.

## Guarantees

- Complete validation before persistence
- No partial graph persistence
- Prior graph versions remain immutable
- Semantic equivalence with full rebuild for the supported path
- Explicit rebuild / fallback mode in logs and build results

Assessment runs do not automatically rebuild the enterprise graph. Use
`EnterpriseKnowledgeService.link_latest_assessments(...)` or
`aimf enterprise build --link-assessments` explicitly.
