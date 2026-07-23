"""Repository Graph construction framework (extractors + assembler).

Extractors contribute ``RepositoryExtractionResult`` values. Only
``RepositoryGraphAssembler`` builds and validates ``RepositoryGraph``.
"""

from aimf.services.repository_graph.assembler import (
    RepositoryGraphAssembler,
    RepositoryGraphAssemblyError,
)
from aimf.services.repository_graph.context import RepositoryExtractionContext
from aimf.services.repository_graph.enums import (
    ExtractionDiagnosticSeverity,
    RepositoryExtractionScope,
)
from aimf.services.repository_graph.extractors import (
    MavenDependencyExtractor,
    PackageJsonDependencyExtractor,
    PathBasedModuleResolver,
    RepositoryDependencyExtractor,
    RepositoryStructureExtractor,
)
from aimf.services.repository_graph.protocol import RepositoryGraphExtractor
from aimf.services.repository_graph.results import (
    ExtractionDiagnostic,
    RepositoryExtractionResult,
    RepositoryExtractionStatistics,
)

__all__ = [
    "ExtractionDiagnostic",
    "ExtractionDiagnosticSeverity",
    "MavenDependencyExtractor",
    "PackageJsonDependencyExtractor",
    "PathBasedModuleResolver",
    "RepositoryDependencyExtractor",
    "RepositoryExtractionContext",
    "RepositoryExtractionResult",
    "RepositoryExtractionScope",
    "RepositoryExtractionStatistics",
    "RepositoryGraphAssembler",
    "RepositoryGraphAssemblyError",
    "RepositoryGraphExtractor",
    "RepositoryStructureExtractor",
]
