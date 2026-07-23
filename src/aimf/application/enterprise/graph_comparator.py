"""Semantic comparison of enterprise graphs."""

from __future__ import annotations

from aimf.application.enterprise.models import EnterpriseGraphDiff
from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph


class EnterpriseGraphComparator:
    def compare(
        self,
        left: EnterpriseKnowledgeGraph,
        right: EnterpriseKnowledgeGraph,
    ) -> EnterpriseGraphDiff:
        left_entities = {
            str(item.entity_id): (
                item.kind.value,
                item.name,
                item.description,
                tuple(sorted(item.labels.items())),
            )
            for item in left.entities
            if not item.kind.value.startswith("Codestrata")
        }
        right_entities = {
            str(item.entity_id): (
                item.kind.value,
                item.name,
                item.description,
                tuple(sorted(item.labels.items())),
            )
            for item in right.entities
            if not item.kind.value.startswith("Codestrata")
        }
        left_rels = {
            str(item.relationship_id): (
                item.kind.value,
                item.source_entity_id.root,
                item.target_entity_id.root,
            )
            for item in left.relationships
        }
        right_rels = {
            str(item.relationship_id): (
                item.kind.value,
                item.source_entity_id.root,
                item.target_entity_id.root,
            )
            for item in right.relationships
        }
        added_e = tuple(sorted(set(right_entities) - set(left_entities)))
        removed_e = tuple(sorted(set(left_entities) - set(right_entities)))
        modified_e = tuple(
            sorted(
                key
                for key in set(left_entities) & set(right_entities)
                if left_entities[key] != right_entities[key]
            )
        )
        added_r = tuple(sorted(set(right_rels) - set(left_rels)))
        removed_r = tuple(sorted(set(left_rels) - set(right_rels)))
        modified_r = tuple(
            sorted(
                key for key in set(left_rels) & set(right_rels) if left_rels[key] != right_rels[key]
            )
        )
        left_links = set(left.repository_links)
        right_links = set(right.repository_links)
        return EnterpriseGraphDiff(
            left_graph_id=left.graph_id,
            right_graph_id=right.graph_id,
            entities_added=added_e,
            entities_removed=removed_e,
            entities_modified=modified_e,
            relationships_added=added_r,
            relationships_removed=removed_r,
            relationships_modified=modified_r,
            repository_resolutions_changed=tuple(sorted(left_links ^ right_links)),
        )
