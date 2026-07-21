"""Detect common application architecture patterns."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from aimf.models import (
    AnalyzerResult,
    Evidence,
    Finding,
    FindingCategory,
    FindingSource,
    Repository,
    RepositoryFacts,
    Severity,
    Technology,
)
from aimf.models.normalized_facts import ArchitectureFacts, StructureFacts


class ArchitectureAnalyzer:
    """Detect repository architecture using deterministic path conventions."""

    _CONTROLLER_MARKERS = {
        "controller",
        "controllers",
        "resource",
        "resources",
        "endpoint",
        "endpoints",
    }

    _SERVICE_MARKERS = {
        "service",
        "services",
        "business",
        "usecase",
        "usecases",
    }

    _REPOSITORY_MARKERS = {
        "repository",
        "repositories",
        "dao",
        "daos",
        "persistence",
    }

    _DOMAIN_MARKERS = {
        "domain",
        "model",
        "models",
        "entity",
        "entities",
    }

    _CONFIG_MARKERS = {
        "config",
        "configuration",
    }

    _API_MARKERS = {
        "api",
        "rest",
        "graphql",
    }

    _TEST_MARKERS = {
        "test",
        "tests",
        "__tests__",
        "spec",
        "specs",
    }

    _MICROSERVICE_MARKERS = {
        "services",
        "microservices",
        "apps",
        "packages",
    }

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
        facts: RepositoryFacts | None = None,
    ) -> AnalyzerResult:
        """Analyze repository paths for architectural patterns."""

        del technologies
        del facts

        component_paths: dict[str, list[str]] = {
            "controllers": [],
            "services": [],
            "repositories": [],
            "domain": [],
            "configuration": [],
            "apis": [],
            "tests": [],
        }

        top_level_directories: Counter[str] = Counter()

        for relative_path in repository.files:
            normalized_path = relative_path.replace("\\", "/")
            path_parts = [part.lower() for part in normalized_path.split("/") if part]

            if not path_parts:
                continue

            if len(path_parts) > 1:
                top_level_directories[path_parts[0]] += 1

            self._classify_path(
                relative_path=normalized_path,
                path_parts=path_parts,
                component_paths=component_paths,
            )

        findings: list[Finding] = []

        findings.extend(self._detect_layered_architecture(component_paths))
        findings.extend(self._detect_api_layer(component_paths))
        findings.extend(self._detect_persistence_layer(component_paths))
        findings.extend(self._detect_test_structure(component_paths))
        findings.extend(
            self._detect_repository_shape(
                component_paths=component_paths,
                top_level_directories=top_level_directories,
            )
        )

        has_api_layer = bool(component_paths["controllers"] or component_paths["apis"])
        has_service_layer = bool(component_paths["services"])
        has_persistence_layer = bool(component_paths["repositories"])
        has_domain_layer = bool(component_paths["domain"])
        has_tests = bool(component_paths["tests"])

        application_directories = sorted(
            directory
            for directory in top_level_directories
            if directory in self._MICROSERVICE_MARKERS
        )
        is_multi_application = bool(application_directories)
        application_count = len(application_directories) if is_multi_application else 1

        architecture_layers = [
            layer
            for layer, present in (
                ("api", has_api_layer),
                ("service", has_service_layer),
                ("persistence", has_persistence_layer),
                ("domain", has_domain_layer),
                ("tests", has_tests),
            )
            if present
        ]

        return AnalyzerResult(
            findings=findings,
            facts=RepositoryFacts(
                structure=StructureFacts(
                    application_count=application_count,
                    has_tests=has_tests,
                    architecture_layers=architecture_layers,
                ),
                architecture=ArchitectureFacts(
                    has_api_layer=has_api_layer,
                    has_service_layer=has_service_layer,
                    has_persistence_layer=has_persistence_layer,
                    has_domain_layer=has_domain_layer,
                    is_multi_application=is_multi_application,
                ),
            ),
        )

    def _classify_path(
        self,
        relative_path: str,
        path_parts: list[str],
        component_paths: dict[str, list[str]],
    ) -> None:
        """Classify a repository path into architectural components."""

        path_tokens = set(path_parts)

        if path_tokens & self._CONTROLLER_MARKERS:
            component_paths["controllers"].append(relative_path)

        if path_tokens & self._SERVICE_MARKERS:
            component_paths["services"].append(relative_path)

        if path_tokens & self._REPOSITORY_MARKERS:
            component_paths["repositories"].append(relative_path)

        if path_tokens & self._DOMAIN_MARKERS:
            component_paths["domain"].append(relative_path)

        if path_tokens & self._CONFIG_MARKERS:
            component_paths["configuration"].append(relative_path)

        if path_tokens & self._API_MARKERS:
            component_paths["apis"].append(relative_path)

        if path_tokens & self._TEST_MARKERS:
            component_paths["tests"].append(relative_path)

    def _detect_layered_architecture(
        self,
        component_paths: dict[str, list[str]],
    ) -> list[Finding]:
        """Detect controller-service-repository layering."""

        layers = {
            layer
            for layer in (
                "controllers",
                "services",
                "repositories",
            )
            if component_paths[layer]
        }

        if len(layers) < 2:
            return []

        return [
            self._finding(
                rule_id="ARCH001",
                title="Layered application architecture detected",
                severity=Severity.INFO,
                evidence=("Detected architectural layers: " + ", ".join(sorted(layers))),
                metadata={
                    "layers": sorted(layers),
                    "controller_count": len(component_paths["controllers"]),
                    "service_count": len(component_paths["services"]),
                    "repository_count": len(component_paths["repositories"]),
                },
            )
        ]

    def _detect_api_layer(
        self,
        component_paths: dict[str, list[str]],
    ) -> list[Finding]:
        """Detect an API or controller layer."""

        api_paths = {
            *component_paths["controllers"],
            *component_paths["apis"],
        }

        if not api_paths:
            return []

        return [
            self._finding(
                rule_id="ARCH002",
                title="API layer detected",
                severity=Severity.INFO,
                evidence=(f"Detected {len(api_paths)} API-related files"),
                metadata={
                    "file_count": len(api_paths),
                    "sample_paths": sorted(api_paths)[:10],
                },
            )
        ]

    def _detect_persistence_layer(
        self,
        component_paths: dict[str, list[str]],
    ) -> list[Finding]:
        """Detect repository, DAO, or persistence components."""

        repository_paths = component_paths["repositories"]

        if not repository_paths:
            return []

        return [
            self._finding(
                rule_id="ARCH003",
                title="Persistence layer detected",
                severity=Severity.INFO,
                evidence=(f"Detected {len(repository_paths)} persistence-related files"),
                metadata={
                    "file_count": len(repository_paths),
                    "sample_paths": repository_paths[:10],
                },
            )
        ]

    def _detect_test_structure(
        self,
        component_paths: dict[str, list[str]],
    ) -> list[Finding]:
        """Detect repository test organization."""

        test_paths = component_paths["tests"]

        if not test_paths:
            return [
                self._finding(
                    rule_id="ARCH004",
                    title="No conventional test structure detected",
                    severity=Severity.LOW,
                    evidence=(
                        "No files were found under conventional test or specification directories"
                    ),
                    metadata={
                        "test_file_count": 0,
                    },
                )
            ]

        return [
            self._finding(
                rule_id="ARCH005",
                title="Test structure detected",
                severity=Severity.INFO,
                evidence=(f"Detected {len(test_paths)} files under test-related directories"),
                metadata={
                    "test_file_count": len(test_paths),
                    "sample_paths": test_paths[:10],
                },
            )
        ]

    def _detect_repository_shape(
        self,
        component_paths: dict[str, list[str]],
        top_level_directories: Counter[str],
    ) -> list[Finding]:
        """Infer monolith or multi-application repository structure."""

        application_directories = {
            directory
            for directory in top_level_directories
            if directory in self._MICROSERVICE_MARKERS
        }

        architectural_components = sum(
            bool(component_paths[component])
            for component in (
                "controllers",
                "services",
                "repositories",
                "domain",
            )
        )

        if application_directories:
            return [
                self._finding(
                    rule_id="ARCH006",
                    title="Multi-application repository structure detected",
                    severity=Severity.INFO,
                    evidence=(
                        "Detected multi-application directories: "
                        + ", ".join(sorted(application_directories))
                    ),
                    metadata={
                        "directories": sorted(application_directories),
                    },
                )
            ]

        if architectural_components >= 2:
            return [
                self._finding(
                    rule_id="ARCH007",
                    title="Single-application architecture detected",
                    severity=Severity.INFO,
                    evidence=(
                        "Architectural components appear within "
                        "one repository application structure"
                    ),
                    metadata={
                        "component_count": (architectural_components),
                    },
                )
            ]

        return []

    def _finding(
        self,
        rule_id: str,
        title: str,
        severity: Severity,
        evidence: str,
        metadata: dict[str, object],
    ) -> Finding:
        """Create an architecture finding."""

        sample_paths = metadata.get("sample_paths")
        file_path = "."

        if isinstance(sample_paths, list) and sample_paths:
            first_path = sample_paths[0]
            if isinstance(first_path, str):
                file_path = first_path

        return Finding(
            rule_id=rule_id,
            title=title,
            description=evidence,
            category=FindingCategory.ARCHITECTURE,
            severity=severity,
            source=FindingSource.STATIC_ANALYSIS,
            evidence=[
                Evidence(
                    file_path=file_path,
                    description=evidence,
                )
            ],
            affected_technologies=[],
            metadata=metadata,
        )
