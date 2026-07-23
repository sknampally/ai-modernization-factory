"""Phase 3 enterprise knowledge tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aimf.application.enterprise.errors import (
    EnterpriseManifestLoadError,
    EnterpriseManifestParseError,
)
from aimf.application.enterprise.factory import (
    PassthroughRepositoryIdentityResolver,
    create_enterprise_knowledge_service,
    create_enterprise_query_service,
)
from aimf.application.enterprise.graph_comparator import EnterpriseGraphComparator
from aimf.application.enterprise.models import EnterprisePolicy
from aimf.domain.enterprise.enums import EnterpriseEntityKind, EnterpriseRelationshipKind
from aimf.domain.enterprise.identifiers import build_entity_id, build_relationship_id
from aimf.infrastructure.enterprise.workspace import EnterpriseWorkspaceWriter
from aimf.infrastructure.enterprise.yaml_loader import YamlEnterpriseManifestSource


def test_domain_avoids_yaml_and_transport_imports() -> None:
    root = Path("src/aimf/domain/enterprise")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import yaml" not in text
        assert "typer" not in text
        assert "fastmcp" not in text
        assert "sqlite3" not in text
        assert "subprocess" not in text


def test_application_avoids_typer_fastmcp_sqlite() -> None:
    root = Path("src/aimf/application/enterprise")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "typer" not in text
        assert "fastmcp" not in text
        assert "sqlite3" not in text
        assert "import yaml" not in text


def test_identity_deterministic() -> None:
    assert build_entity_id(EnterpriseEntityKind.APPLICATION, "SIS") == (
        "application:sis"
    )
    rel = build_relationship_id(
        EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
        "application:sis",
        "repository:api",
    )
    assert rel.startswith("rel:APPLICATION_USES_REPOSITORY:")


def test_init_validate_build_query(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    writer = EnterpriseWorkspaceWriter()
    created = writer.create_workspace(str(workspace), examples=True, force=False)
    assert "enterprise.yaml" in created

    policy = EnterprisePolicy(
        require_registered_repositories=False,
        allow_unresolved_repositories=True,
    )
    service = create_enterprise_knowledge_service(
        policy=policy,
        resolver=PassthroughRepositoryIdentityResolver(),
        knowledge_directory=tmp_path / "knowledge",
    )
    validation = service.validate_workspace(str(workspace))
    assert validation.status == "passed", validation.errors

    built = service.build_graph(str(workspace))
    assert built.graph.enterprise_id == "enterprise:acme"
    assert len(built.graph.entities) >= 10
    assert len(built.graph.relationships) >= 5

    queries = create_enterprise_query_service(
        policy=policy, knowledge_directory=tmp_path / "knowledge"
    )
    apps = queries.list_entities(
        kind=EnterpriseEntityKind.APPLICATION,
        enterprise_id="enterprise:acme",
    )
    assert any(item.entity_id == "application:student-information-system" for item in apps)

    repos = queries.list_by_relationship(
        source_id="application:student-information-system",
        kind=EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
        enterprise_id="enterprise:acme",
    )
    assert any(item.entity_id == "repository:student-api" for item in repos)

    impact = queries.repository_context(
        "repository:student-api", enterprise_id="enterprise:acme"
    )
    assert impact.impacted_entities


def test_unsafe_yaml_constructor_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    workspace.mkdir()
    (workspace / "enterprise.yaml").write_text(
        "!!python/object/apply:os.system ['echo pwned']\n",
        encoding="utf-8",
    )
    loader = YamlEnterpriseManifestSource(policy=EnterprisePolicy())
    with pytest.raises(
        (EnterpriseManifestParseError, EnterpriseManifestLoadError, yaml.YAMLError)
    ):
        loader.load(str(workspace))


def test_secret_field_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace), examples=False)
    bad = workspace / "applications" / "bad.yaml"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: Application
metadata:
  id: bad-app
  name: Bad App
spec:
  password: super-secret
""",
        encoding="utf-8",
    )
    service = create_enterprise_knowledge_service(
        policy=EnterprisePolicy(
            require_registered_repositories=False,
            allow_unresolved_repositories=True,
        ),
        knowledge_directory=tmp_path / "knowledge",
    )
    result = service.validate_workspace(str(workspace))
    assert result.status == "failed"
    assert any(issue.code == "suspicious_secret_field" for issue in result.errors)


def test_credential_url_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace), examples=False)
    repo = workspace / "repositories" / "bad.yaml"
    repo.parent.mkdir(parents=True, exist_ok=True)
    repo.write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: RepositoryReference
metadata:
  id: bad-repo
  name: Bad Repo
spec:
  remoteUrl: https://user:token@github.com/acme/bad
""",
        encoding="utf-8",
    )
    service = create_enterprise_knowledge_service(
        policy=EnterprisePolicy(
            require_registered_repositories=False,
            allow_unresolved_repositories=True,
        ),
        knowledge_directory=tmp_path / "knowledge",
    )
    result = service.validate_workspace(str(workspace))
    assert any(issue.code == "credential_bearing_url" for issue in result.errors)


def test_graph_compare_and_immutability(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace), examples=True)
    policy = EnterprisePolicy(
        require_registered_repositories=False,
        allow_unresolved_repositories=True,
    )
    service = create_enterprise_knowledge_service(
        policy=policy,
        resolver=PassthroughRepositoryIdentityResolver(),
        knowledge_directory=tmp_path / "knowledge",
    )
    first = service.build_graph(str(workspace)).graph
    # Modify one entity name
    app = workspace / "applications" / "student-information-system.yaml"
    payload = yaml.safe_load(app.read_text(encoding="utf-8"))
    payload["metadata"]["name"] = "SIS Renamed"
    app.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    second = service.build_graph(str(workspace)).graph
    assert first.graph_id != second.graph_id
    # Prior graph still readable
    loaded = service.get_graph(first.graph_id)
    assert loaded.graph_id == first.graph_id
    diff = EnterpriseGraphComparator().compare(first, second)
    assert "application:student-information-system" in diff.entities_modified


def test_enterprise_settings_default(tmp_path: Path) -> None:
    from aimf.config import load_settings

    config = tmp_path / "aimf.toml"
    config.write_text(
        """
        [repository]
        path = "examples/sample-js-app"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config)
    assert settings.enterprise.enabled is False
    assert settings.enterprise.workspace == "enterprise"
