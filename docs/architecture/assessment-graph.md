"""Architectural decision: Assessment Graph as a projection/reference graph.

Status: Accepted for the Assessment Graph foundation
Date: 2026-07-22

Context
-------
AIMF already has two peer immutable graphs:

* **Repository Graph (RG)** — observations about one repository (files, modules,
  dependencies, symbols).
* **Engineering Knowledge Graph (EKG)** — reusable engineering concepts
  (technologies, patterns, practices, rules) with no repository identity.

The Knowledge Pipeline produces an immutable ``KnowledgeBindingResult`` that
links RG observations to EKG concepts without mutating either source graph.

Assessment work (rules, findings, risks, recommendations) needs a place to
attach assessment-scoped structure and evidence. Absorbing bindings into RG or
EKG would either pollute reusable knowledge with repository facts or couple
repository inventory to curated catalogs.

Decision
--------
Introduce a third graph — the **Assessment Graph (AG)** — scoped to one
assessment. It is a **projection/reference graph**, not a copy of RG or EKG.

1. Why a separate graph
~~~~~~~~~~~~~~~~~~~~~~~
RG owns repository facts. EKG owns reusable knowledge. Assessment owns the
*join* between them for a specific run, plus future assessment outcomes.
Keeping AG separate preserves immutability and ownership boundaries, enables
fail-closed validation against source fingerprints, and avoids inserting
repository-specific facts into EKG.

2. What the Assessment Graph owns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Lightweight **reference nodes** to RG entities and EKG concepts (identity
  pointers only; not duplicated source payloads).
* Typed **binding relationships** (for example ``binds_to_knowledge``) that
  carry binding identity, matching metadata, evidence references, and
  provenance from ``KnowledgeBindingResult``.
* Assessment-scoped identity: deterministic ``graph_id`` and
  ``source_fingerprint`` derived from RG identity/fingerprint, EKG
  identity/fingerprint, and the normalized binding set.
* (Future) attachment points for rules, findings, risks, and recommendations.

3. What remains owned by the Repository Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Repository identity, inventory, files, modules, dependencies, symbols, and all
RG relationship topology. AG never mutates RG and does not re-encode full RG
property payloads.

4. What remains owned by the Engineering Knowledge Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reusable concepts, catalog relationships, aliases, lifecycle/maturity metadata,
and curated rules/strategies. AG never mutates EKG and never inserts repository
identity or assessment outcomes into EKG.

5. How AG consumes ``KnowledgeBindingResult``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An application builder validates that the supplied RG and EKG match the binding
result's recorded graph IDs and source fingerprints, that every bound node
exists, then projects accepted bindings into AG reference nodes and
relationships. Duplicate bindings collapse to the same AG elements. Unknown or
mismatched inputs fail closed.

6. How source graph IDs and fingerprints are preserved
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Binding results record RG/EKG ``graph_id`` and ``source_fingerprint``.
* AG reference-node properties retain source graph IDs and source node IDs.
* AG ``source_fingerprint`` and ``graph_id`` are deterministic digests of those
  inputs plus sorted binding IDs. No timestamps, paths, or UUID4 values.

7. How evidence is represented
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Evidence stays as ``EvidenceReference`` values on AG relationships (and
serialized binding property bags where needed). Evidence points at repository
observations; it does not embed large file bodies.

8. Future rules, findings, risks, and recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Later phases may add assessment-scoped node/relationship types that attach to
binding relationships or reference nodes. Those outcomes live only on AG (or
downstream report models), never on EKG, and do not rewrite RG.

9. Why repository-specific information must never enter EKG
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
EKG is a reusable catalog shared across assessments. Repository facts would make
catalog identity assessment-dependent, break catalog versioning, and destroy
deterministic reuse. Bindings and assessments belong in the pipeline result and
AG.

10. Deterministic assessment identity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The same logical RG, EKG, and binding set always yield the same AG
serialization, ``graph_id``, and ``source_fingerprint``. Changing RG content,
EKG catalog version, or any binding changes the AG fingerprint.

Non-goals (this foundation)
---------------------------
* Rule execution, findings generation, recommendations
* Agents, embeddings, Neo4j, or additional AI calls
* Copying full RG/EKG subgraphs into AG
* Mutating RG, EKG, or ``KnowledgeBindingResult``
