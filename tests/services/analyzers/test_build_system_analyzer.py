"""Tests for the build system analyzer."""

from aimf.models import Repository
from aimf.services.analyzers.build_system_analyzer import BuildSystemAnalyzer


def test_detects_maven_build_system() -> None:
    repository = Repository(
        name="sample-maven-project",
        source="local",
        path="/tmp/sample-maven-project",
        files=[
            "pom.xml",
            "mvnw",
            ".mvn/wrapper/maven-wrapper.properties",
            "src/main/java/com/example/Application.java",
        ],
    )

    analyzer = BuildSystemAnalyzer()

    result = analyzer.analyze(
        repository=repository,
        technologies=[],
    )
    findings = result.findings

    assert len(findings) == 1


def test_detects_multiple_build_systems() -> None:
    repository = Repository(
        name="full-stack-project",
        source="local",
        path="/tmp/sample-maven-project",
        files=[
            "backend/pom.xml",
            "backend/mvnw",
            "frontend/package.json",
            "frontend/package-lock.json",
        ],
    )

    analyzer = BuildSystemAnalyzer()

    result = analyzer.analyze(
        repository=repository,
        technologies=[],
    )
    findings = result.findings
    finding = findings[0]

    assert finding.metadata["build_systems"] == ["maven", "npm"]
    assert finding.metadata["build_files"] == [
        "backend/pom.xml",
        "frontend/package.json",
    ]
    assert finding.metadata["wrapper_files"] == ["backend/mvnw"]
    assert finding.metadata["lock_files"] == [
        "frontend/package-lock.json",
    ]
    assert finding.metadata["multiple_build_systems"] is True


def test_returns_empty_build_facts_when_no_build_system_is_detected() -> None:
    repository = Repository(
        name="documentation-project",
        source="local",
        path="/tmp/sample-maven-project",
        files=[
            "README.md",
            "docs/architecture.md",
        ],
    )

    analyzer = BuildSystemAnalyzer()

    result = analyzer.analyze(
        repository=repository,
        technologies=[],
    )
    findings = result.findings
    finding = findings[0]

    assert finding.metadata == {
        "build_systems": [],
        "build_files": [],
        "wrapper_files": [],
        "lock_files": [],
        "multiple_build_systems": False,
    }
    assert finding.evidence == []
    assert "No supported build system" in finding.description
