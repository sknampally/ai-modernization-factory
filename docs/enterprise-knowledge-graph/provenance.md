# Provenance

Every enterprise entity and relationship records provenance.

| Category | Meaning |
|----------|---------|
| `declared_yaml` | Stated in enterprise YAML |
| `resolved_repository_registry` | Matched to CodeStrata registry identity |
| `derived_repository_graph` | From repository graph (future/selective) |
| `derived_knowledge_graph` | From engineering knowledge graph |
| `derived_assessment_graph` | From assessment graph |
| `derived_finding` | Propagated from a finding |
| `derived_recommendation` | Propagated from a recommendation |
| `system_generated` | Platform bookkeeping |

Queries and `aimf enterprise explain` distinguish declared vs derived knowledge.
Do not treat derived impact as authoritative architecture.
