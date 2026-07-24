# Architecture Limitations (4.2.1 / 4.2.1a)

1. **Repository Graph alone** lacks package→package import edges; the pack builds
   an application-layer `ArchitectureAnalysisView` from source text.
2. **Layer classification** uses path markers with confidence; low-confidence or
   ambiguous classification yields not applicable for direction/boundary rules.
3. **Unit selection** collapses nested packages; some genuine nested boundaries
   may be under-reported until declared module maps exist.
4. **Service-level cycles** deferred — no distinct higher-level service graph.
5. **Framework leakage** covers a small initial Java pattern set only.
6. **Positive strengths** are not yet emitted as first-class findings.
7. **No production scoring** and **no CTO report redesign**.
8. **Enterprise rule** only enforces explicitly declared `prohibited_frameworks`.
9. **Composition-root cycles** are omitted by design; review wiring separately if needed.
10. Package rename (`aimf` → `codestrata`) and CLI rename remain deferred.
