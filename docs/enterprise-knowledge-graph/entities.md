# Enterprise entity kinds

All manifests share the envelope:

```yaml
apiVersion: codestrata.io/v1alpha1
kind: <Kind>
metadata:
  id: <stable-id>
  name: <display-name>
  description: optional
  labels: {}
  annotations: {}
spec: {}
```

Canonical entity IDs use `kind-prefix:metadata.id` (for example
`application:student-information-system`). Display names may change; IDs must not.

## Required kinds (Phase 3)

| Kind | Prefix | Purpose |
|------|--------|---------|
| Enterprise | `enterprise:` | Root workspace |
| Organization | `organization:` | Org hierarchy |
| BusinessDomain | `domain:` | Business domains |
| BusinessCapability | `capability:` | Capabilities |
| Application | `application:` | Enterprise systems |
| RepositoryReference | `repository:` | Links to CodeStrata repos |
| Service | `service:` | Runtime services |
| API | `api:` | Exposed/consumed APIs |
| DataStore | `data-store:` | Databases and stores |
| MessageChannel | `message-channel:` | Topics/queues |
| Team | `team:` | Ownership teams |
| Person | `person:` | Limited ownership contacts |
| Environment | `environment:` | Deploy environments |
| CloudResource | `cloud-resource:` | Lightweight cloud inventory |
| TechnologyStandard | `technology-standard:` | Tech standards |
| ArchitectureStandard | `architecture-standard:` | Architecture standards |
| ModernizationInitiative | `initiative:` | Modernization programs |

Graph projections (not YAML kinds) may add CodestrataRepository, Snapshot,
AssessmentRun, Finding, and Recommendation nodes when assessments are linked.

## Security

Do not put passwords, tokens, private keys, or credential-bearing URLs in YAML.
Suspicious keys are rejected during validation.

See [relationships.md](relationships.md) and [security.md](security.md).
