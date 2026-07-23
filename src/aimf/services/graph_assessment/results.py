"""Immutable result of the Phase 2 graph assessment pipeline."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from aimf.domain.assessment_graph import AssessmentGraph
from aimf.domain.engineering_knowledge import EngineeringKnowledgeGraph
from aimf.domain.knowledge_binding import KnowledgeBindingResult
from aimf.domain.repository import RepositoryManifest
from aimf.domain.repository_graph import RepositoryGraph


class GraphAssessmentPipelineResult(BaseModel):
    """Deterministic Phase 2 artifacts produced for one assessment.

    Graph wrappers are arbitrary types preserved by Pydantic; the result object
    itself is frozen and must not mutate source graphs.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    manifest: RepositoryManifest
    repository_graph: RepositoryGraph
    knowledge_graph: EngineeringKnowledgeGraph
    binding_result: KnowledgeBindingResult
    assessment_graph: AssessmentGraph
