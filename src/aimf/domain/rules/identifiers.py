"""Stable rule identity helpers for the Shared Rule Platform."""

from __future__ import annotations

import re

from pydantic import RootModel, field_validator

# Shared platform: category.kebab-case-name
_SHARED_RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+$")
# Legacy Assessment Graph rules: aimf-rule-*
_LEGACY_RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")


def validate_rule_id(value: str) -> str:
    """Validate and normalize a machine-safe rule ID.

    Accepts Shared Rule Platform IDs (``namespace.name``) and legacy Assessment
    Graph IDs (``aimf-rule-*``) so adapters can preserve finding identity.
    """

    compact = value.strip().lower()
    if not compact:
        raise ValueError("rule_id must be non-blank")
    if _SHARED_RULE_ID_PATTERN.fullmatch(compact) or _LEGACY_RULE_ID_PATTERN.fullmatch(compact):
        return compact
    raise ValueError(
        "rule_id must use namespace.kebab-name form "
        "(example: architecture.layer-dependency) or a legacy aimf-rule-* id"
    )


class RuleId(RootModel[str]):
    """Stable rule identity (not a UUID; not derived from class names)."""

    root: str

    @field_validator("root", mode="before")
    @classmethod
    def validate_root(cls, value: object) -> str:
        return validate_rule_id(str(value))

    def __str__(self) -> str:
        return self.root

    def __hash__(self) -> int:
        return hash(self.root)
