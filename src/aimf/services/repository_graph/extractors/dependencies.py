"""Repository Graph dependency extractors (Maven POM + package.json)."""

from __future__ import annotations

from collections.abc import Sequence

from aimf.domain.graph.enums import ProvenanceSource
from aimf.domain.graph.models import EvidenceReference, GraphNode, GraphRelationship, Provenance
from aimf.domain.repository.files import RepositoryFileEntry
from aimf.domain.repository_graph.dependencies import Dependency
from aimf.domain.repository_graph.enums import RepositoryRelationshipType
from aimf.domain.repository_graph.factories import RepositoryGraphNodeFactory
from aimf.domain.repository_graph.ids import RepositoryNodeIdFactory
from aimf.domain.repository_graph.properties import DependencyProperties
from aimf.domain.repository_graph.relationship_factory import RepositoryRelationshipFactory
from aimf.services.repository_graph.context import RepositoryExtractionContext
from aimf.services.repository_graph.enums import (
    ExtractionDiagnosticSeverity,
    RepositoryExtractionScope,
)
from aimf.services.repository_graph.extractors.maven_parser import (
    is_malformed_maven_pom,
    parse_maven_dependencies,
)
from aimf.services.repository_graph.extractors.package_json_parser import (
    is_malformed_package_json,
    parse_package_json_dependencies,
)
from aimf.services.repository_graph.results import (
    ExtractionDiagnostic,
    RepositoryExtractionResult,
    RepositoryExtractionStatistics,
)

MAVEN_DEPENDENCY_EXTRACTOR_ID = "repository-graph:maven-dependencies"
PACKAGE_JSON_DEPENDENCY_EXTRACTOR_ID = "repository-graph:package-json-dependencies"
REPOSITORY_DEPENDENCY_EXTRACTOR_ID = "repository-graph:dependencies"

_EXTRACTOR_VERSION = "1.0.0"


class MavenDependencyExtractor:
    """Extract Maven dependency nodes from ``pom.xml`` inventory files."""

    def __init__(self, *, extractor_version: str = _EXTRACTOR_VERSION) -> None:
        self._extractor_version = extractor_version

    @property
    def extractor_id(self) -> str:
        return MAVEN_DEPENDENCY_EXTRACTOR_ID

    def extract(self, context: RepositoryExtractionContext) -> RepositoryExtractionResult:
        return _extract_from_manifests(
            context=context,
            extractor_id=self.extractor_id,
            extractor_version=self._extractor_version,
            basename="pom.xml",
            parse=parse_maven_dependencies,
            is_malformed=is_malformed_maven_pom,
            malformed_code="maven_pom_malformed",
            provenance_source_id="inventory:maven-dependencies",
        )


class PackageJsonDependencyExtractor:
    """Extract npm dependency nodes from ``package.json`` inventory files."""

    def __init__(self, *, extractor_version: str = _EXTRACTOR_VERSION) -> None:
        self._extractor_version = extractor_version

    @property
    def extractor_id(self) -> str:
        return PACKAGE_JSON_DEPENDENCY_EXTRACTOR_ID

    def extract(self, context: RepositoryExtractionContext) -> RepositoryExtractionResult:
        return _extract_from_manifests(
            context=context,
            extractor_id=self.extractor_id,
            extractor_version=self._extractor_version,
            basename="package.json",
            parse=parse_package_json_dependencies,
            is_malformed=is_malformed_package_json,
            malformed_code="package_json_malformed",
            provenance_source_id="inventory:package-json-dependencies",
        )


class RepositoryDependencyExtractor:
    """Composite extractor that merges Maven and package.json contributions."""

    def __init__(
        self,
        *,
        maven_extractor: MavenDependencyExtractor | None = None,
        package_json_extractor: PackageJsonDependencyExtractor | None = None,
        extractor_version: str = _EXTRACTOR_VERSION,
    ) -> None:
        self._maven = maven_extractor or MavenDependencyExtractor(
            extractor_version=extractor_version
        )
        self._package_json = package_json_extractor or PackageJsonDependencyExtractor(
            extractor_version=extractor_version
        )
        self._extractor_version = extractor_version

    @property
    def extractor_id(self) -> str:
        return REPOSITORY_DEPENDENCY_EXTRACTOR_ID

    def extract(self, context: RepositoryExtractionContext) -> RepositoryExtractionResult:
        parts = (
            self._maven.extract(context),
            self._package_json.extract(context),
        )
        nodes = _unique_nodes(tuple(node for part in parts for node in part.nodes))
        relationships = _unique_relationships(
            tuple(rel for part in parts for rel in part.relationships)
        )
        diagnostics = tuple(
            sorted(
                (diag for part in parts for diag in part.diagnostics),
                key=lambda item: (item.code, item.path or "", item.message),
            )
        )
        provenance = (
            Provenance(
                source_type=ProvenanceSource.DETERMINISTIC_ANALYZER,
                source_id="inventory:repository-dependencies",
                extractor_id=self.extractor_id,
                extractor_version=self._extractor_version,
            ),
        )
        return RepositoryExtractionResult(
            extractor_id=self.extractor_id,
            nodes=nodes,
            relationships=relationships,
            diagnostics=diagnostics,
            statistics=RepositoryExtractionStatistics(
                extractor_id=self.extractor_id,
                node_count=len(nodes),
                relationship_count=len(relationships),
                diagnostic_count=len(diagnostics),
                duration_ms=None,
            ),
            provenance=provenance,
            deleted_repository_paths=(),
        )


def _extract_from_manifests(
    *,
    context: RepositoryExtractionContext,
    extractor_id: str,
    extractor_version: str,
    basename: str,
    parse: object,
    is_malformed: object,
    malformed_code: str,
    provenance_source_id: str,
) -> RepositoryExtractionResult:
    from collections.abc import Callable

    parse_fn: Callable[..., tuple[Dependency, ...]] = parse  # type: ignore[assignment]
    malformed_fn: Callable[[bytes], bool] = is_malformed  # type: ignore[assignment]

    provenance = Provenance(
        source_type=ProvenanceSource.DETERMINISTIC_ANALYZER,
        source_id=provenance_source_id,
        extractor_id=extractor_id,
        extractor_version=extractor_version,
    )
    repository_key = context.manifest.identity.repository_key
    node_factory = RepositoryGraphNodeFactory(repository_key)
    relationship_factory = RepositoryRelationshipFactory()
    repository_node_id = RepositoryNodeIdFactory(repository_key).repository()

    selected = _selected_manifest_entries(context, basename=basename)
    nodes: list[GraphNode] = []
    relationships: list[GraphRelationship] = []
    diagnostics: list[ExtractionDiagnostic] = []

    for entry in selected:
        path = entry.path.root
        try:
            content = context.content_reader.read(path).data
        except (OSError, FileNotFoundError, ValueError) as error:
            diagnostics.append(
                ExtractionDiagnostic(
                    severity=ExtractionDiagnosticSeverity.WARNING,
                    code="dependency_manifest_unreadable",
                    message=f"unable to read dependency manifest: {error}",
                    path=path,
                    extractor_id=extractor_id,
                )
            )
            continue

        if malformed_fn(content):
            diagnostics.append(
                ExtractionDiagnostic(
                    severity=ExtractionDiagnosticSeverity.WARNING,
                    code=malformed_code,
                    message=f"malformed dependency manifest ignored: {path}",
                    path=path,
                    extractor_id=extractor_id,
                )
            )
            continue

        facts = parse_fn(content, source_file=path)
        for fact in facts:
            node = _dependency_node(node_factory, fact, provenance)
            nodes.append(node)
            relationships.append(
                relationship_factory.create(
                    relationship_type=RepositoryRelationshipType.DEPENDS_ON,
                    source_node_id=repository_node_id,
                    target_node_id=node.id,
                    provenance=(provenance,),
                    evidence=(
                        EvidenceReference(
                            evidence_type="dependency_manifest",
                            source_id=f"file:{path}",
                            path=path,
                            excerpt=(
                                f"{fact.ecosystem}:{fact.namespace or '_'}:"
                                f"{fact.name}@{fact.version_raw or 'unspecified'}"
                            ),
                        ),
                    ),
                )
            )

    unique_nodes = _unique_nodes(tuple(nodes))
    unique_relationships = _unique_relationships(tuple(relationships))
    ordered_diagnostics = tuple(
        sorted(
            diagnostics,
            key=lambda item: (item.code, item.path or "", item.message),
        )
    )
    return RepositoryExtractionResult(
        extractor_id=extractor_id,
        nodes=unique_nodes,
        relationships=unique_relationships,
        diagnostics=ordered_diagnostics,
        statistics=RepositoryExtractionStatistics(
            extractor_id=extractor_id,
            node_count=len(unique_nodes),
            relationship_count=len(unique_relationships),
            diagnostic_count=len(ordered_diagnostics),
            duration_ms=None,
        ),
        provenance=(provenance,),
        deleted_repository_paths=(),
    )


def _selected_manifest_entries(
    context: RepositoryExtractionContext,
    *,
    basename: str,
) -> tuple[RepositoryFileEntry, ...]:
    needle = basename.lower()
    entries = [
        entry
        for entry in context.manifest.files
        if entry.path.root.rsplit("/", 1)[-1].lower() == needle
    ]
    if context.scope is RepositoryExtractionScope.FULL:
        return tuple(sorted(entries, key=lambda item: item.path.root))

    assert context.change_set is not None
    changed = {
        path.root
        for path in (
            *context.change_set.added_paths,
            *context.change_set.modified_paths,
            *context.change_set.metadata_changed_paths,
        )
    }
    return tuple(
        sorted(
            (entry for entry in entries if entry.path.root in changed),
            key=lambda item: item.path.root,
        )
    )


def _dependency_node(
    node_factory: RepositoryGraphNodeFactory,
    fact: Dependency,
    provenance: Provenance,
) -> GraphNode:
    return node_factory.dependency(
        DependencyProperties(
            ecosystem=fact.ecosystem,
            name=fact.name,
            namespace=fact.namespace,
            version=fact.version_raw,
            scope=fact.scope,
            direct=fact.direct,
            source_file=fact.source_file,
        ),
        provenance=(provenance,),
        evidence=(
            EvidenceReference(
                evidence_type="dependency_manifest",
                source_id=f"file:{fact.source_file}",
                path=fact.source_file,
                excerpt=(
                    f"{fact.ecosystem}:{fact.namespace or '_'}:"
                    f"{fact.name}@{fact.version_raw or 'unspecified'}"
                ),
            ),
        ),
    )


def _unique_nodes(nodes: Sequence[GraphNode]) -> tuple[GraphNode, ...]:
    merged: dict[str, GraphNode] = {}
    for node in nodes:
        existing = merged.get(node.id.root)
        if existing is None:
            merged[node.id.root] = node
            continue
        if existing != node:
            # Prefer versioned properties when merging across sections/extractors.
            left_version = existing.properties.get("version")
            right_version = node.properties.get("version")
            if left_version in (None, "") and right_version not in (None, ""):
                merged[node.id.root] = node
            elif left_version not in (None, "") and right_version in (None, ""):
                continue
            elif (
                existing.properties.get("direct") is False and node.properties.get("direct") is True
            ):
                merged[node.id.root] = node
            elif existing == node:
                continue
            else:
                # Deterministic: keep lexicographically smaller JSON-ish property set.
                if sorted(node.properties.items()) < sorted(existing.properties.items()):
                    merged[node.id.root] = node
    return tuple(merged[key] for key in sorted(merged))


def _unique_relationships(
    relationships: Sequence[GraphRelationship],
) -> tuple[GraphRelationship, ...]:
    merged: dict[str, GraphRelationship] = {}
    for relationship in relationships:
        existing = merged.get(relationship.id)
        if existing is None or existing == relationship:
            merged[relationship.id] = relationship
            continue
        # Same identity with different evidence should not occur for DEPENDS_ON;
        # keep the first for stability.
        merged.setdefault(relationship.id, relationship)
    return tuple(merged[key] for key in sorted(merged))
