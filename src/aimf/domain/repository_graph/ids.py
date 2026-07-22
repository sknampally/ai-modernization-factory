"""Deterministic Repository Graph node identity construction.

Identity rules (language-neutral, storage-independent):

- ``repository_key`` is an explicitly supplied stable key (not a raw URL with
  credentials, and not a display name alone).
- File identities use repository-relative POSIX paths; absolute paths and
  ``..`` traversal segments are rejected.
- Qualified names and signatures are normalized (strip) but not language-parsed.
- Callable identities include owner plus signature so overloads stay distinct.
- Dependency identities include ecosystem and coordinates but omit version so
  version upgrades preserve logical identity.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from aimf.domain.graph.ids import NodeId
from aimf.domain.graph.validation import require_nonblank

_ABSOLUTE_WINDOWS = re.compile(r"^[A-Za-z]:[/\\]")


def normalize_repository_key(value: str) -> str:
    """Normalize and validate a stable repository identity key."""

    key = require_nonblank(value, label="repository_key")
    # Reject URL/credential shapes so IDs never embed access material.
    if "://" in key or "@" in key:
        raise ValueError("repository_key must not contain URLs or credential material")
    if any(ch in key for ch in ("/", "\\", ":")):
        raise ValueError("repository_key must not contain path separators or ':' characters")
    return key


def normalize_repository_relative_path(value: str) -> str:
    """Return a repository-relative POSIX path suitable for file identities."""

    raw = require_nonblank(value, label="path")
    normalized = raw.replace("\\", "/")
    if normalized.startswith("/") or _ABSOLUTE_WINDOWS.match(normalized):
        raise ValueError("path must be repository-relative, not absolute")

    path = PurePosixPath(normalized)
    parts = path.parts
    if not parts or parts == (".",):
        raise ValueError("path must not be blank after normalization")
    if any(part == ".." for part in parts):
        raise ValueError("path must not contain '..' traversal segments")

    cleaned_parts = [part for part in parts if part not in ("", ".")]
    if not cleaned_parts:
        raise ValueError("path must not be blank after normalization")
    return "/".join(cleaned_parts)


def normalize_qualified_name(value: str, *, label: str) -> str:
    """Strip a qualified name without applying language-specific parsing."""

    return require_nonblank(value, label=label)


def normalize_dependency_namespace(value: str | None) -> str:
    """Normalize an optional dependency namespace; ``_`` marks absence."""

    if value is None:
        return "_"
    compact = require_nonblank(value, label="dependency namespace")
    if compact == "_":
        return "_"
    return compact


class RepositoryNodeIdFactory:
    """Build deterministic ``NodeId`` values for Repository Graph nodes."""

    def __init__(self, repository_key: str) -> None:
        self._repository_key = normalize_repository_key(repository_key)

    @property
    def repository_key(self) -> str:
        return self._repository_key

    def repository(self) -> NodeId:
        return NodeId(f"repo:{self._repository_key}")

    def module(self, module_key: str) -> NodeId:
        key = require_nonblank(module_key, label="module_key")
        if any(ch in key for ch in ("/", "\\")):
            raise ValueError("module_key must not contain path separators")
        return NodeId(f"repo:{self._repository_key}:module:{key}")

    def file(self, relative_path: str) -> NodeId:
        path = normalize_repository_relative_path(relative_path)
        return NodeId(f"repo:{self._repository_key}:file:{path}")

    def namespace(self, qualified_name: str) -> NodeId:
        name = normalize_qualified_name(qualified_name, label="qualified_name")
        return NodeId(f"repo:{self._repository_key}:namespace:{name}")

    def type(self, qualified_name: str) -> NodeId:
        name = normalize_qualified_name(qualified_name, label="qualified_name")
        return NodeId(f"repo:{self._repository_key}:type:{name}")

    def callable(self, *, qualified_owner: str, signature: str) -> NodeId:
        owner = normalize_qualified_name(qualified_owner, label="qualified_owner")
        sig = require_nonblank(signature, label="signature")
        return NodeId(f"repo:{self._repository_key}:callable:{owner}#{sig}")

    def dependency(
        self,
        *,
        ecosystem: str,
        name: str,
        namespace: str | None = None,
    ) -> NodeId:
        eco = require_nonblank(ecosystem, label="ecosystem")
        dep_name = require_nonblank(name, label="dependency name")
        group = normalize_dependency_namespace(namespace)
        return NodeId(f"repo:{self._repository_key}:dependency:{eco}:{group}:{dep_name}")
