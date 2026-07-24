"""Application configuration loaded from a TOML file."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

from aimf.config.dotenv import load_dotenv
from aimf.repository_auth.exceptions import UnsupportedRepositoryUrlError
from aimf.repository_auth.github_urls import parse_github_repository_url
from aimf.repository_auth.models import RepositoryAuthenticationConfig


class RepositorySettings(BaseModel):
    """Configuration for the repository being analyzed.

    Provide at least one of:

    * ``url`` — GitHub HTTPS/SSH URL (required for ``aimf scan``)
    * ``path`` — local filesystem path (supported by ``aimf assess``)
    """

    url: str | None = None
    path: str | None = None
    branch: str | None = None
    authentication: RepositoryAuthenticationConfig | None = None

    @field_validator("url")
    @classmethod
    def validate_repository_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        if not compact:
            raise ValueError("repository.url must be a nonempty GitHub URL")
        # Validate shape at configuration load time; do not resolve credentials.
        parse_github_repository_url(compact)
        return compact

    @field_validator("path")
    @classmethod
    def validate_repository_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        if not compact:
            raise ValueError("repository.path must be a nonempty local path")
        if "://" in compact:
            raise ValueError(
                "repository.path must be a local filesystem path, not a URL. "
                "Use repository.url for GitHub repositories."
            )
        return compact

    @model_validator(mode="after")
    def require_url_or_path(self) -> RepositorySettings:
        if self.url is None and self.path is None:
            raise ValueError(
                "Configure repository.url (GitHub) or repository.path (local). "
                'Example: path = "examples/sample-js-app" or '
                'url = "https://github.com/org/repo"'
            )
        return self


class WorkspaceSettings(BaseModel):
    """Configuration for the local analysis workspace."""

    directory: Path = Path(".aimf-workspace")
    clean_before_clone: bool = True


class PmdSettings(BaseModel):
    """Configuration for the PMD static-analysis provider."""

    enabled: bool = True
    executable: str = "pmd"
    profile: str = "standard"
    rulesets: list[str] = Field(
        default_factory=lambda: [
            "category/java/bestpractices.xml",
            "category/java/errorprone.xml",
            "category/java/design.xml",
        ]
    )
    minimum_priority: int = 5
    timeout_seconds: int = 120

    @field_validator("executable")
    @classmethod
    def validate_executable(cls, value: str) -> str:
        compact = value.strip()
        if not compact:
            raise ValueError("PMD executable must be a nonempty string")
        if any(character in compact for character in [";", "|", "&", "`", "$", "\n"]):
            raise ValueError("PMD executable must not contain shell metacharacters")
        return compact

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, value: str) -> str:
        from aimf.static_analysis.providers.pmd_profiles import parse_pmd_profile

        return parse_pmd_profile(value).value

    @field_validator("rulesets")
    @classmethod
    def validate_rulesets(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("PMD rulesets must not be empty")
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("PMD rulesets must be nonempty strings")
            cleaned.append(item.strip())
        return cleaned

    @field_validator("minimum_priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("PMD minimum_priority must be between 1 and 5")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("PMD timeout_seconds must be a positive integer")
        return value


class StaticAnalysisProviderSettings(BaseModel):
    """Provider-specific static-analysis settings."""

    pmd: PmdSettings = Field(default_factory=PmdSettings)


class StaticAnalysisSettings(BaseModel):
    """Top-level static-analysis subsystem settings."""

    enabled: bool = False
    fail_on_provider_error: bool = False
    pmd: PmdSettings = Field(default_factory=PmdSettings)

    @model_validator(mode="before")
    @classmethod
    def coerce_nested_pmd(cls, value: object) -> object:
        """Allow both [static_analysis.pmd] nesting styles from TOML."""

        if not isinstance(value, dict):
            return value
        # tomllib may provide pmd as nested table already.
        return value


class AwsSettings(BaseModel):
    """Optional AWS session settings for Bedrock and related services.

    Prefer configuring profile/region here so users do not need to export
    ``AWS_PROFILE`` or ``AWS_REGION`` before running ``aimf assess --with-ai``.
    """

    profile: str | None = None
    region: str | None = None

    @field_validator("profile", "region")
    @classmethod
    def validate_optional_nonempty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        return compact or None


class BedrockSettings(BaseModel):
    """Optional AWS Bedrock settings for modernization assessment."""

    model_id: str | None = None
    region: str | None = None

    @field_validator("model_id", "region")
    @classmethod
    def validate_optional_nonempty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        return compact or None


DEFAULT_BEDROCK_MODEL_ID = "amazon.nova-lite-v1:0"
DEFAULT_BEDROCK_PROVIDER = "bedrock"


class AiSettings(BaseModel):
    """Optional AI subsystem settings."""

    provider: str = "bedrock"
    bedrock: BedrockSettings = Field(default_factory=BedrockSettings)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        compact = value.strip().lower()
        if not compact:
            raise ValueError("ai.provider must be a nonempty string")
        return compact


class KnowledgeSettings(BaseModel):
    """Local engineering knowledge store settings.

    The knowledge store is independent of report retention under ``reports/``.
    """

    directory: Path = Path(".aimf/knowledge")


class McpSettings(BaseModel):
    """Optional FastMCP server settings.

    Omitted ``[mcp]`` sections use these defaults. The server is a local
    developer tool (stdio); it is not intended for untrusted public exposure.
    """

    enabled: bool = True
    transport: str = "stdio"
    log_level: str = "INFO"

    @field_validator("transport")
    @classmethod
    def validate_transport(cls, value: str) -> str:
        compact = value.strip().lower()
        if compact != "stdio":
            raise ValueError("mcp.transport currently supports only 'stdio'")
        return compact

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        compact = value.strip().upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if compact not in allowed:
            raise ValueError(f"mcp.log_level must be one of {sorted(allowed)}")
        return compact


class AgentsSettings(BaseModel):
    """Optional Agent Framework bounds.

    Omitted ``[agents]`` sections use conservative defaults. Model-provider
    settings remain under ``[ai]`` / ``[aws]``.
    """

    enabled: bool = True
    max_steps: int = 10
    max_findings: int = 100
    max_recommendations: int = 100
    max_components: int = 100
    dependency_depth: int = 2
    stop_on_blocking_validation: bool = True
    include_ai_context: bool = True
    fail_on_missing_required_artifact: bool = True

    @field_validator("max_steps")
    @classmethod
    def validate_max_steps(cls, value: int) -> int:
        if value < 1 or value > 20:
            raise ValueError("agents.max_steps must be between 1 and 20")
        return value

    @field_validator("max_findings", "max_recommendations", "max_components")
    @classmethod
    def validate_positive_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("agent collection limits must be positive")
        return value

    @field_validator("dependency_depth")
    @classmethod
    def validate_dependency_depth(cls, value: int) -> int:
        if value < 1 or value > 3:
            raise ValueError("agents.dependency_depth must be between 1 and 3")
        return value


class IncrementalSettings(BaseModel):
    """Optional incremental assessment planning and execution bounds.

    ``rollout_mode`` defaults to ``off``. Neither legacy booleans nor rollout
    activate incremental execution for ``aimf assess``. Hard safety fallbacks
    cannot be disabled. ``allow_ai_reuse`` must remain false in Phase 2F.3.
    """

    rollout_mode: str = "off"
    enabled: bool = False
    execution_enabled: bool = False
    max_changed_files: int = 100
    max_change_ratio: float = 0.30
    dependency_depth: int = 2
    max_impacted_components: int = 500
    max_impacted_findings: int = 500
    max_impacted_recommendations: int = 500
    allow_metadata_only_noop: bool = True
    require_complete_fingerprints: bool = True
    fallback_on_unknown_impact: bool = True
    fallback_on_unsupported_language: bool = True
    fallback_on_engine_change: bool = True
    allow_selective_scan: bool = True
    allow_graph_merge: bool = True
    allow_rule_reuse: bool = True
    allow_recommendation_reuse: bool = True
    allow_ai_reuse: bool = False
    fallback_on_step_failure: bool = True
    fallback_on_merge_conflict: bool = True
    fallback_on_validation_failure: bool = True
    validate_after_execution: bool = True
    persist_execution_records: bool = True
    enable_equivalence_check: bool = False
    max_explanations: int = 500
    max_equivalence_differences: int = 100
    fallback_on_metric_inconsistency: bool = True

    @field_validator(
        "max_changed_files",
        "max_impacted_components",
        "max_impacted_findings",
        "max_impacted_recommendations",
        "max_explanations",
        "max_equivalence_differences",
    )
    @classmethod
    def validate_positive_bounds(cls, value: int) -> int:
        if value < 1:
            raise ValueError("incremental bounds must be positive")
        return value

    @field_validator("max_change_ratio")
    @classmethod
    def validate_change_ratio(cls, value: float) -> float:
        if value <= 0.0 or value > 1.0:
            raise ValueError("incremental.max_change_ratio must be in (0.0, 1.0]")
        return value

    @field_validator("dependency_depth")
    @classmethod
    def validate_dependency_depth(cls, value: int) -> int:
        if value < 1 or value > 3:
            raise ValueError("incremental.dependency_depth must be between 1 and 3")
        return value

    @field_validator("rollout_mode")
    @classmethod
    def validate_rollout_mode(cls, value: str) -> str:
        compact = value.strip().lower()
        allowed = {"off", "plan_only", "opt_in", "default_with_fallback"}
        if compact not in allowed:
            raise ValueError(f"incremental.rollout_mode must be one of {sorted(allowed)}")
        return compact

    @model_validator(mode="before")
    @classmethod
    def map_legacy_booleans(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        mode = data.get("rollout_mode")
        if mode is None or (isinstance(mode, str) and not mode.strip()):
            if data.get("execution_enabled"):
                return {**data, "rollout_mode": "opt_in"}
            if data.get("enabled"):
                return {**data, "rollout_mode": "plan_only"}
        return data

    @field_validator("require_complete_fingerprints", "fallback_on_unknown_impact")
    @classmethod
    def validate_hard_safety(cls, value: bool) -> bool:
        if not value:
            raise ValueError(
                "incremental.require_complete_fingerprints and "
                "fallback_on_unknown_impact are hard safety conditions and must be true"
            )
        return value

    @field_validator(
        "fallback_on_step_failure",
        "fallback_on_merge_conflict",
        "fallback_on_validation_failure",
        "fallback_on_metric_inconsistency",
    )
    @classmethod
    def validate_execution_hard_safety(cls, value: bool) -> bool:
        if not value:
            raise ValueError("incremental execution fallback hard-safety flags must remain true")
        return value

    @field_validator("allow_ai_reuse")
    @classmethod
    def validate_ai_reuse_disabled(cls, value: bool) -> bool:
        if value:
            raise ValueError("incremental.allow_ai_reuse must be false in Phase 2F.3")
        return value

    @model_validator(mode="after")
    def validate_rollout_consistency(self) -> IncrementalSettings:
        mode = self.rollout_mode
        if mode == "off" and (self.enabled or self.execution_enabled):
            raise ValueError(
                "Conflicting incremental settings: rollout_mode=off with "
                "enabled/execution_enabled true"
            )
        if mode == "plan_only" and self.execution_enabled:
            raise ValueError("Conflicting incremental settings: plan_only with execution_enabled")
        return self


class EnterpriseSettings(BaseModel):
    """Optional Enterprise Knowledge Graph settings (disabled by default)."""

    enabled: bool = False
    workspace: str = "enterprise"
    schema_version: str = "codestrata.io/v1alpha1"
    persist_graph: bool = True
    link_repository_assessments: bool = True
    require_registered_repositories: bool = True
    allow_unresolved_repositories: bool = False
    unknown_fields: str = "error"
    max_manifest_files: int = 5000
    max_manifest_size_bytes: int = 1_048_576
    max_yaml_depth: int = 50
    max_graph_entities: int = 100_000
    max_graph_relationships: int = 500_000
    max_query_results: int = 500
    max_traversal_depth: int = 5
    max_dependency_paths: int = 100
    persist_manifest_snapshot: bool = True

    @field_validator(
        "max_manifest_files",
        "max_manifest_size_bytes",
        "max_yaml_depth",
        "max_graph_entities",
        "max_graph_relationships",
        "max_query_results",
        "max_traversal_depth",
        "max_dependency_paths",
    )
    @classmethod
    def validate_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("enterprise bounds must be positive")
        return value

    @field_validator("max_traversal_depth")
    @classmethod
    def validate_depth(cls, value: int) -> int:
        if value > 10:
            raise ValueError("enterprise.max_traversal_depth cannot exceed 10")
        return value

    @field_validator("unknown_fields")
    @classmethod
    def validate_unknown_fields(cls, value: str) -> str:
        compact = value.strip().lower()
        if compact not in {"error", "warn", "ignore"}:
            raise ValueError("enterprise.unknown_fields must be error|warn|ignore")
        return compact

    @model_validator(mode="after")
    def validate_resolution_policy(self) -> EnterpriseSettings:
        if self.require_registered_repositories and self.allow_unresolved_repositories:
            # Allowed combination: require attempt but permit unresolved as warning
            # when allow_unresolved_repositories is true — keep as-is.
            pass
        return self


class ArchitectureRuleToggle(BaseModel):
    """Per-rule enablement toggle (enabled when parent pack is active)."""

    enabled: bool = True


_DEFAULT_COMPOSITION_ROOT_MARKERS = (
    "cli",
    "main",
    "bootstrap",
    "boot",
    "entrypoint",
    "entrypoints",
    "__main__",
    "wiring",
    "assemble",
    "assembly",
)
_DEFAULT_REGISTRATION_MARKERS = (
    "registry",
    "registration",
    "di",
    "inject",
    "injector",
    "plugin",
    "plugins",
    "factory",
)


class ExcessiveCouplingRuleSettings(BaseModel):
    """Thresholds for architecture.excessive-cross-module-coupling."""

    enabled: bool = True
    outgoing_module_threshold: int = 8
    minimum_module_count: int = 5
    relative_multiplier: float = 2.0
    exclude_composition_roots: bool = True

    @field_validator("outgoing_module_threshold", "minimum_module_count")
    @classmethod
    def validate_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("coupling thresholds must be positive integers")
        return value

    @field_validator("outgoing_module_threshold")
    @classmethod
    def validate_outgoing_cap(cls, value: int) -> int:
        if value > 10_000:
            raise ValueError("outgoing_module_threshold cannot exceed 10000")
        return value

    @field_validator("relative_multiplier")
    @classmethod
    def validate_relative(cls, value: float) -> float:
        if value < 1.0 or value > 20.0:
            raise ValueError("relative_multiplier must be in [1.0, 20.0]")
        return value


class ArchitectureUnitSelectionSettings(BaseModel):
    """Architectural-unit selection policy for Architecture Intelligence."""

    module_depth: int = 2
    composition_root_markers: list[str] = Field(
        default_factory=lambda: sorted(_DEFAULT_COMPOSITION_ROOT_MARKERS)
    )
    registration_markers: list[str] = Field(
        default_factory=lambda: sorted(_DEFAULT_REGISTRATION_MARKERS)
    )
    ignore_path_markers: list[str] = Field(
        default_factory=lambda: ["/generated/", "/.generated/", "/vendor/"]
    )

    @field_validator("module_depth")
    @classmethod
    def validate_depth(cls, value: int) -> int:
        if value < 1 or value > 8:
            raise ValueError("module_depth must be between 1 and 8")
        return value


class ComponentConcentrationRuleSettings(BaseModel):
    """Thresholds for architecture.component-concentration."""

    enabled: bool = True
    incident_edge_share_threshold: float = 0.30
    minimum_component_count: int = 5

    @field_validator("incident_edge_share_threshold")
    @classmethod
    def validate_share(cls, value: float) -> float:
        if value <= 0.0 or value > 1.0:
            raise ValueError("incident_edge_share_threshold must be in (0, 1]")
        return value

    @field_validator("minimum_component_count")
    @classmethod
    def validate_minimum(cls, value: int) -> int:
        if value < 1:
            raise ValueError("minimum_component_count must be a positive integer")
        return value


class ArchitectureRulesSettings(BaseModel):
    """Architecture Intelligence pack settings (disabled by default; Phase 4.2)."""

    enabled: bool = False
    unit_selection: ArchitectureUnitSelectionSettings = Field(
        default_factory=ArchitectureUnitSelectionSettings
    )
    dependency_cycle: ArchitectureRuleToggle = Field(default_factory=ArchitectureRuleToggle)
    invalid_dependency_direction: ArchitectureRuleToggle = Field(
        default_factory=ArchitectureRuleToggle
    )
    layer_boundary_violation: ArchitectureRuleToggle = Field(
        default_factory=ArchitectureRuleToggle
    )
    excessive_cross_module_coupling: ExcessiveCouplingRuleSettings = Field(
        default_factory=ExcessiveCouplingRuleSettings
    )
    component_concentration: ComponentConcentrationRuleSettings = Field(
        default_factory=ComponentConcentrationRuleSettings
    )
    framework_leakage: ArchitectureRuleToggle = Field(default_factory=ArchitectureRuleToggle)
    service_dependency_cycle: ArchitectureRuleToggle = Field(
        default_factory=ArchitectureRuleToggle
    )
    enterprise_standard_mismatch: ArchitectureRuleToggle = Field(
        default_factory=ArchitectureRuleToggle
    )


class RulesSettings(BaseModel):
    """Shared Rule Platform settings (disabled by default; Phase 4.1)."""

    enabled: bool = False
    fail_on_rule_error: bool = False
    max_rules_per_run: int = 1000
    max_matches_per_rule: int = 1000
    max_total_matches: int = 10_000
    max_evidence_per_match: int = 100
    default_categories: list[str] = Field(default_factory=list)
    architecture: ArchitectureRulesSettings = Field(default_factory=ArchitectureRulesSettings)

    @field_validator(
        "max_rules_per_run",
        "max_matches_per_rule",
        "max_total_matches",
        "max_evidence_per_match",
    )
    @classmethod
    def validate_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("rules bounds must be positive")
        return value

    @field_validator("max_rules_per_run")
    @classmethod
    def validate_max_rules(cls, value: int) -> int:
        if value > 100_000:
            raise ValueError("rules.max_rules_per_run cannot exceed 100000")
        return value

    @field_validator("max_total_matches")
    @classmethod
    def validate_max_matches(cls, value: int) -> int:
        if value > 1_000_000:
            raise ValueError("rules.max_total_matches cannot exceed 1000000")
        return value

    @model_validator(mode="after")
    def validate_architecture_requires_platform(self) -> RulesSettings:
        # Architecture pack may be configured while platform disabled; assess ignores it.
        _ = self.architecture
        return self


_DEFAULT_LANGUAGE_PROVIDER_PRECEDENCE = (
    "language.python.core",
    "language.java.core",
    "language.javascript.core",
)


class LanguageProviderToggle(BaseModel):
    """Enable/disable a single language evidence provider."""

    enabled: bool = True


class LanguageEvidenceProvidersSettings(BaseModel):
    """Provider selection and execution policy."""

    auto_detect: bool = True
    fail_fast: bool = False
    precedence: list[str] = Field(
        default_factory=lambda: list(_DEFAULT_LANGUAGE_PROVIDER_PRECEDENCE)
    )

    @field_validator("precedence")
    @classmethod
    def validate_precedence(cls, value: list[str]) -> list[str]:
        known = set(_DEFAULT_LANGUAGE_PROVIDER_PRECEDENCE)
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            compact = item.strip().lower()
            if not compact:
                continue
            if compact not in known:
                raise ValueError(f"Unknown language evidence provider in precedence: {item}")
            if compact in seen:
                raise ValueError(f"Duplicate provider in precedence: {compact}")
            seen.add(compact)
            cleaned.append(compact)
        return cleaned or list(_DEFAULT_LANGUAGE_PROVIDER_PRECEDENCE)


class LanguageEvidenceSettings(BaseModel):
    """Language Evidence Provider pipeline (disabled by default; Phase 4.2.2)."""

    enabled: bool = False
    providers: LanguageEvidenceProvidersSettings = Field(
        default_factory=LanguageEvidenceProvidersSettings
    )
    python: LanguageProviderToggle = Field(default_factory=LanguageProviderToggle)
    java: LanguageProviderToggle = Field(default_factory=LanguageProviderToggle)
    javascript: LanguageProviderToggle = Field(default_factory=LanguageProviderToggle)


class EvidenceSettings(BaseModel):
    """Evidence collection settings."""

    language: LanguageEvidenceSettings = Field(default_factory=LanguageEvidenceSettings)


class ArchitectureConclusionPolicyToggles(BaseModel):
    """Per-policy enablement for Architecture Conclusions (Phase 4.2.3)."""

    boundary_integrity: bool = True
    cyclic_dependency_structure: bool = True
    broad_dependency_surface: bool = True
    framework_boundary_erosion: bool = True
    enterprise_nonconformance: bool = True
    positive_boundary_conformance: bool = False
    insufficient_evidence: bool = True


class ArchitectureConclusionAggregationSettings(BaseModel):
    group_by_scope: bool = True
    group_related_rules: bool = True
    preserve_standalone_findings: bool = True


class ArchitectureConclusionsSettings(BaseModel):
    """Architecture Conclusions layer (disabled by default; Phase 4.2.3)."""

    enabled: bool = False
    policies: ArchitectureConclusionPolicyToggles = Field(
        default_factory=ArchitectureConclusionPolicyToggles
    )
    aggregation: ArchitectureConclusionAggregationSettings = Field(
        default_factory=ArchitectureConclusionAggregationSettings
    )


class AnalysisSettings(BaseModel):
    """Analysis enrichment settings (optional layers)."""

    architecture_conclusions: ArchitectureConclusionsSettings = Field(
        default_factory=ArchitectureConclusionsSettings
    )


class ArchitectureAssessmentSectionSettings(BaseModel):
    """Architecture assessment section integration (disabled by default; Phase 4.2.4)."""

    enabled: bool = False
    include_findings: bool = True
    include_conclusions: bool = True
    include_recommendation_groups: bool = True
    include_coverage: bool = True
    include_limitations: bool = True
    include_traceability: bool = True
    include_execution_summary: bool = True


class AssessmentSectionsSettings(BaseModel):
    architecture: ArchitectureAssessmentSectionSettings = Field(
        default_factory=ArchitectureAssessmentSectionSettings
    )


class AssessmentSettings(BaseModel):
    """Formal assessment composition settings."""

    sections: AssessmentSectionsSettings = Field(
        default_factory=AssessmentSectionsSettings
    )


class ArchitectureReportSectionSettings(BaseModel):
    """Architecture section in HTML/JSON reports (disabled by default; Phase 4.2.5)."""

    enabled: bool = False
    include_executive_summary: bool = True
    include_metrics: bool = True
    include_conclusions: bool = True
    include_recommendation_groups: bool = True
    include_findings: bool = True
    include_coverage: bool = True
    include_limitations: bool = True
    include_traceability: bool = True
    include_strengths: bool = True


class ReportSectionsSettings(BaseModel):
    architecture: ArchitectureReportSectionSettings = Field(
        default_factory=ArchitectureReportSectionSettings
    )


class ReportSettings(BaseModel):
    """Customer report presentation settings."""

    sections: ReportSectionsSettings = Field(default_factory=ReportSectionsSettings)


class AimfSettings(BaseModel):
    """Top-level AIMF application settings."""

    repository: RepositorySettings
    workspace: WorkspaceSettings = Field(
        default_factory=WorkspaceSettings,
    )
    knowledge: KnowledgeSettings = Field(
        default_factory=KnowledgeSettings,
    )
    static_analysis: StaticAnalysisSettings = Field(
        default_factory=StaticAnalysisSettings,
    )
    aws: AwsSettings = Field(default_factory=AwsSettings)
    ai: AiSettings = Field(default_factory=AiSettings)
    mcp: McpSettings = Field(default_factory=McpSettings)
    agents: AgentsSettings = Field(default_factory=AgentsSettings)
    incremental: IncrementalSettings = Field(default_factory=IncrementalSettings)
    enterprise: EnterpriseSettings = Field(default_factory=EnterpriseSettings)
    rules: RulesSettings = Field(default_factory=RulesSettings)
    evidence: EvidenceSettings = Field(default_factory=EvidenceSettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    assessment: AssessmentSettings = Field(default_factory=AssessmentSettings)
    report: ReportSettings = Field(default_factory=ReportSettings)


def load_settings(config_path: Path) -> AimfSettings:
    """Load AIMF settings from a TOML configuration file.

    Automatically loads a nearby ``.env`` file (if present) before reading
    configuration so environment-variable references such as
    ``AIMF_GITHUB_TOKEN`` resolve without requiring ``source .env``.
    """

    resolved_config = config_path.expanduser()
    load_dotenv(start_directory=resolved_config.parent)
    load_dotenv(start_directory=Path.cwd())

    if not resolved_config.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {resolved_config}\n\n"
            "Fix: create aimf.toml in the project root (see README), or pass "
            "--config /path/to/aimf.toml"
        )

    if not resolved_config.is_file():
        raise ValueError(f"Configuration path is not a file: {resolved_config}")

    with resolved_config.open("rb") as config_file:
        config_data = tomllib.load(config_file)

    try:
        return AimfSettings.model_validate(config_data)
    except Exception as error:
        raise ValueError(
            f"Invalid configuration in {resolved_config}: {error}\n\n"
            "Fix: check [repository] url/path and other settings against the README."
        ) from error


def configured_repository_source(settings: AimfSettings) -> str | None:
    """Return the configured assess/scan repository source, if any.

    Preference for configuration-only resolution: local ``path``, then ``url``.
    """

    if settings.repository.path:
        return settings.repository.path
    if settings.repository.url:
        return settings.repository.url
    return None


def is_github_repository_source(source: str) -> bool:
    """Return whether ``source`` is a GitHub repository URL."""

    try:
        parse_github_repository_url(source)
    except UnsupportedRepositoryUrlError:
        return False
    return True
