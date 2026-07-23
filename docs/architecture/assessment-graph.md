# Assessment Graph (ADR pointer)

Canonical documentation: [../assessment-graph.md](../assessment-graph.md).

This file previously held the full ADR. Content was consolidated to avoid
duplication. Key decisions remain:

* AG is a projection/reference graph for one assessment
* RG owns repository facts; EKG owns reusable knowledge
* AG never mutates RG or EKG; fail-closed fingerprint validation
* Downstream: Rule Engine → Recommendation Engine → optional AI / reports
