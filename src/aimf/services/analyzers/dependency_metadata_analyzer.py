"""Extract dependency metadata from supported manifest files."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from pathlib import Path

from aimf.models import (
    AnalyzerResult,
    Dependency,
    DependencyFacts,
    Repository,
    RepositoryFacts,
    Technology,
)


class DependencyMetadataAnalyzer:
    """Extract direct dependencies from repository manifests."""

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
        facts: RepositoryFacts | None = None,
    ) -> AnalyzerResult:
        """Parse supported dependency manifests."""

        del technologies
        del facts

        dependencies: list[Dependency] = []

        for relative_path in repository.files:
            manifest_path = repository.path / relative_path

            if relative_path.endswith("pom.xml"):
                dependencies.extend(
                    self._parse_maven(
                        manifest_path=manifest_path,
                        relative_path=relative_path,
                    )
                )

            elif relative_path.endswith("package.json"):
                dependencies.extend(
                    self._parse_npm(
                        manifest_path=manifest_path,
                        relative_path=relative_path,
                    )
                )

        dependencies.sort(
            key=lambda dependency: (
                dependency.ecosystem,
                dependency.manifest_path,
                dependency.name,
                dependency.scope,
            )
        )

        return AnalyzerResult(
            findings=[],
            facts=RepositoryFacts(
                dependencies=self._build_dependency_facts(dependencies)
            ),
        )

    def _parse_maven(
        self,
        manifest_path: Path,
        relative_path: str,
    ) -> list[Dependency]:
        """Parse direct dependencies from a Maven POM."""

        if not manifest_path.is_file():
            return []

        try:
            root = ET.parse(manifest_path).getroot()
        except (ET.ParseError, OSError):
            return []

        namespace = self._xml_namespace(root)
        properties = self._maven_properties(root, namespace)

        dependencies: list[Dependency] = []

        dependencies_element = root.find(
            self._xml_path(namespace, "dependencies")
        )

        if dependencies_element is None:
            return []

        for dependency_element in dependencies_element.findall(
            self._xml_path(namespace, "dependency")
        ):
            group_id = self._xml_text(
                dependency_element,
                namespace,
                "groupId",
            )
            artifact_id = self._xml_text(
                dependency_element,
                namespace,
                "artifactId",
            )

            if not artifact_id:
                continue

            name = (
                f"{group_id}:{artifact_id}"
                if group_id
                else artifact_id
            )

            raw_version = self._xml_text(
                dependency_element,
                namespace,
                "version",
            )
            version = self._resolve_maven_property(
                raw_version,
                properties,
            )

            maven_scope = self._xml_text(
                dependency_element,
                namespace,
                "scope",
            )

            scope = self._normalize_maven_scope(maven_scope)

            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem="maven",
                    scope=scope,
                    manifest_path=relative_path,
                    categories=self._classify_dependency(
                        name=name,
                        ecosystem="maven",
                    ),
                    dynamic_version=self._is_dynamic_maven_version(
                        raw_version
                    ),
                    unmanaged_version=raw_version is None,
                )
            )

        return dependencies

    def _parse_npm(
        self,
        manifest_path: Path,
        relative_path: str,
    ) -> list[Dependency]:
        """Parse dependencies from an npm package.json file."""

        if not manifest_path.is_file():
            return []

        try:
            package_data = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return []

        if not isinstance(package_data, dict):
            return []

        dependency_sections = {
            "dependencies": "runtime",
            "devDependencies": "development",
            "peerDependencies": "peer",
            "optionalDependencies": "optional",
        }

        dependencies: list[Dependency] = []

        for section_name, scope in dependency_sections.items():
            section = package_data.get(section_name, {})

            if not isinstance(section, dict):
                continue

            for name, version_value in section.items():
                if not isinstance(name, str):
                    continue

                version = (
                    version_value
                    if isinstance(version_value, str)
                    else None
                )

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        ecosystem="npm",
                        scope=scope,
                        manifest_path=relative_path,
                        categories=self._classify_dependency(
                            name=name,
                            ecosystem="npm",
                        ),
                        dynamic_version=self._is_dynamic_npm_version(
                            version
                        ),
                        unmanaged_version=version is None,
                    )
                )

        return dependencies

    def _build_dependency_facts(
        self,
        dependencies: list[Dependency],
    ) -> DependencyFacts:
        """Build aggregate facts from extracted dependencies."""

        return DependencyFacts(
            dependencies=dependencies,
            direct_dependency_count=len(dependencies),
            development_dependency_count=sum(
                dependency.scope == "development"
                for dependency in dependencies
            ),
            test_dependency_count=sum(
                dependency.scope == "test"
                or "testing" in dependency.categories
                for dependency in dependencies
            ),
            framework_dependencies=self._dependencies_in_category(
                dependencies,
                "framework",
            ),
            database_drivers=self._dependencies_in_category(
                dependencies,
                "database",
            ),
            cloud_sdks=self._dependencies_in_category(
                dependencies,
                "cloud",
            ),
            logging_libraries=self._dependencies_in_category(
                dependencies,
                "logging",
            ),
            testing_libraries=self._dependencies_in_category(
                dependencies,
                "testing",
            ),
            security_libraries=self._dependencies_in_category(
                dependencies,
                "security",
            ),
            dynamic_version_dependencies=[
                dependency.name
                for dependency in dependencies
                if dependency.dynamic_version
            ],
            unmanaged_version_dependencies=[
                dependency.name
                for dependency in dependencies
                if dependency.unmanaged_version
            ],
        )

    def _dependencies_in_category(
        self,
        dependencies: list[Dependency],
        category: str,
    ) -> list[str]:
        """Return dependency names belonging to a category."""

        return list(
            dict.fromkeys(
                dependency.name
                for dependency in dependencies
                if category in dependency.categories
            )
        )

    def _classify_dependency(
        self,
        name: str,
        ecosystem: str,
    ) -> list[str]:
        """Apply deterministic dependency classifications."""

        normalized_name = name.lower()
        categories: list[str] = []

        category_patterns = {
            "framework": (
                "spring-boot",
                "spring-framework",
                "react",
                "angular",
                "vue",
                "next",
                "express",
            ),
            "database": (
                "postgresql",
                "mysql",
                "mariadb",
                "oracle",
                "mongodb",
                "mongoose",
                "hibernate",
                "jdbc",
            ),
            "cloud": (
                "aws-sdk",
                "software.amazon.awssdk",
                "azure",
                "google-cloud",
                "@aws-sdk",
            ),
            "logging": (
                "slf4j",
                "logback",
                "log4j",
                "winston",
                "pino",
            ),
            "testing": (
                "junit",
                "mockito",
                "assertj",
                "jest",
                "vitest",
                "mocha",
                "cypress",
                "playwright",
            ),
            "security": (
                "spring-security",
                "oauth",
                "jwt",
                "jsonwebtoken",
                "passport",
            ),
        }

        for category, patterns in category_patterns.items():
            if any(
                pattern in normalized_name
                for pattern in patterns
            ):
                categories.append(category)

        if ecosystem == "npm" and normalized_name in {
            "react",
            "vue",
            "express",
        }:
            if "framework" not in categories:
                categories.append("framework")

        return categories

    def _maven_properties(
        self,
        root: ET.Element,
        namespace: str,
    ) -> dict[str, str]:
        """Extract Maven project properties."""

        properties_element = root.find(
            self._xml_path(namespace, "properties")
        )

        if properties_element is None:
            return {}

        properties: dict[str, str] = {}

        for child in properties_element:
            property_name = child.tag.split("}")[-1]

            if child.text:
                properties[property_name] = child.text.strip()

        return properties

    def _resolve_maven_property(
        self,
        version: str | None,
        properties: dict[str, str],
    ) -> str | None:
        """Resolve a Maven property-based version when possible."""

        if version is None:
            return None

        match = re.fullmatch(r"\$\{([^}]+)\}", version)

        if match is None:
            return version

        property_name = match.group(1)

        return properties.get(property_name, version)

    def _normalize_maven_scope(
        self,
        scope: str | None,
    ) -> str:
        """Map Maven scopes to normalized AIMF scopes."""

        if scope is None or scope == "compile":
            return "runtime"

        if scope == "test":
            return "test"

        if scope == "provided":
            return "provided"

        if scope == "runtime":
            return "runtime"

        if scope == "system":
            return "system"

        if scope == "import":
            return "import"

        return scope

    def _is_dynamic_maven_version(
        self,
        version: str | None,
    ) -> bool:
        """Determine whether a Maven version is dynamic."""

        if version is None:
            return False

        normalized_version = version.strip().upper()

        return (
            normalized_version in {"LATEST", "RELEASE"}
            or normalized_version.startswith("[")
            or normalized_version.startswith("(")
        )

    def _is_dynamic_npm_version(
        self,
        version: str | None,
    ) -> bool:
        """Determine whether an npm dependency uses a dynamic version."""

        if version is None:
            return False

        normalized_version = version.strip().lower()

        return (
            normalized_version in {"*", "latest", ""}
            or normalized_version.startswith("^")
            or normalized_version.startswith("~")
            or normalized_version.startswith(">")
            or normalized_version.startswith("<")
            or "||" in normalized_version
            or " - " in normalized_version
            or normalized_version.startswith("git")
            or normalized_version.startswith("http")
            or normalized_version.startswith("file:")
        )

    def _xml_namespace(self, root: ET.Element) -> str:
        """Extract an XML namespace from an element tag."""

        if root.tag.startswith("{"):
            return root.tag.split("}")[0][1:]

        return ""

    def _xml_path(
        self,
        namespace: str,
        element_name: str,
    ) -> str:
        """Construct an ElementTree path with an optional namespace."""

        if namespace:
            return f"{{{namespace}}}{element_name}"

        return element_name

    def _xml_text(
        self,
        parent: ET.Element,
        namespace: str,
        element_name: str,
    ) -> str | None:
        """Read and normalize text from a child XML element."""

        element = parent.find(
            self._xml_path(namespace, element_name)
        )

        if element is None or element.text is None:
            return None

        value = element.text.strip()

        return value or None