"""Incremental assessment planning, execution, and operations (Phase 2F).

Phase 2F.1: planning only.
Phase 2F.2: selective execution with full-rebuild fallback.
Phase 2F.3: validation, telemetry, explainability, provenance, CLI/MCP rollout.

Does not change ``aimf assess`` defaults. Incremental execution requires
explicit opt-in via rollout mode ``opt_in`` (or ``assess_incrementally_if_safe``)
and never enables AI artifact reuse.
"""

from __future__ import annotations

from aimf.application.incremental.changes import ChangeClassifier
from aimf.application.incremental.compatibility import CompatibilityEvaluator
from aimf.application.incremental.eligibility import PreviousRunEligibilityChecker
from aimf.application.incremental.equivalence import (
    AssessmentEquivalenceResult,
    AssessmentSemanticComparator,
    CompleteAssessmentArtifacts,
)
from aimf.application.incremental.errors import (
    IncrementalArtifactMergeError,
    IncrementalCompatibilityError,
    IncrementalConfigurationError,
    IncrementalDependencyError,
    IncrementalEligibilityError,
    IncrementalEquivalenceError,
    IncrementalExecutionError,
    IncrementalExecutionRecordNotFoundError,
    IncrementalExplanationError,
    IncrementalFallbackError,
    IncrementalGraphMergeError,
    IncrementalInspectionError,
    IncrementalManifestError,
    IncrementalMergeValidationError,
    IncrementalMetricsError,
    IncrementalPlanningError,
    IncrementalPlanRejectedError,
    IncrementalRecommendationError,
    IncrementalRolloutDisabledError,
    IncrementalRuleExecutionError,
    IncrementalValidationError,
    SelectiveScanError,
)
from aimf.application.incremental.execution import IncrementalAssessmentExecutor
from aimf.application.incremental.execution_models import (
    IncrementalExecutionMode,
    IncrementalExecutionRequest,
    IncrementalExecutionResult,
    IncrementalExecutionStatus,
    IncrementalRecomputeCounts,
    IncrementalReuseCounts,
)
from aimf.application.incremental.execution_policies import (
    IncrementalExecutionPolicy,
    execution_policy_from_settings,
)
from aimf.application.incremental.execution_record import IncrementalExecutionRecord
from aimf.application.incremental.explainability import (
    ExplanationFilters,
    IncrementalExplainabilityService,
    IncrementalExplanation,
    IncrementalExplanationKind,
)
from aimf.application.incremental.factory import (
    AssessmentApplicationServiceRunner,
    create_incremental_assessment_executor,
    create_incremental_operations_service,
    create_incremental_planning_service,
)
from aimf.application.incremental.fingerprints import (
    AssessmentContentFingerprint,
    EngineCompatibilityFingerprint,
    PlanningFileFingerprint,
    assessment_content_fingerprint,
    current_engine_fingerprint,
    planning_file_fingerprint,
)
from aimf.application.incremental.graph_rebuild import (
    merge_graph_snapshots,
    nodes_sourced_from_paths,
)
from aimf.application.incremental.impact import ImpactAnalyzer
from aimf.application.incremental.inspection import IncrementalInspectionService
from aimf.application.incremental.inventory_merge import merge_inventory
from aimf.application.incremental.merge import IncrementalArtifactMerger
from aimf.application.incremental.merge_validation import (
    IncrementalMergeValidator,
    MergedAssessmentPackage,
)
from aimf.application.incremental.metrics import (
    IncrementalExecutionMetrics,
    IncrementalMetricsCalculator,
)
from aimf.application.incremental.models import (
    CandidateRepositoryState,
    CompatibilityResult,
    FileChange,
    FileChangeDimensions,
    FileChangeKind,
    ImpactAnalysis,
    IncrementalAssessmentPlan,
    IncrementalBaseEligibility,
    IncrementalPlanMode,
    IncrementalPlanningRequest,
    IncrementalPlanStep,
    IncrementalStepType,
    RepositoryChangeSet,
    ReuseAssessment,
    ReuseDecision,
)
from aimf.application.incremental.operations import IncrementalOperationsService
from aimf.application.incremental.planner import IncrementalPlanner
from aimf.application.incremental.policies import IncrementalPlanningPolicy, policy_from_settings
from aimf.application.incremental.provenance import (
    FileIncrementalExecutionRecordStore,
    InMemoryIncrementalExecutionRecordStore,
)
from aimf.application.incremental.recommendation_execution import (
    IncrementalRecommendationExecutor,
)
from aimf.application.incremental.reuse import ReusePolicy
from aimf.application.incremental.rollout import (
    IncrementalRolloutMode,
    IncrementalRolloutPolicy,
    resolve_rollout_mode,
    rollout_policy_from_settings,
)
from aimf.application.incremental.rule_execution import (
    DefaultRuleScopeProvider,
    IncrementalRuleExecutor,
)
from aimf.application.incremental.selective_scan import (
    CandidateManifestSelectiveScanService,
    SelectiveScanRequest,
    SelectiveScanResult,
    UnsupportedSelectiveScanService,
)
from aimf.application.incremental.service import IncrementalPlanningService
from aimf.application.incremental.validation import IncrementalValidationService
from aimf.application.incremental.validation_models import (
    IncrementalValidationCheck,
    IncrementalValidationCheckKind,
    IncrementalValidationIssue,
    IncrementalValidationRequest,
    IncrementalValidationResult,
    IncrementalValidationStatus,
)

__all__ = [
    "AssessmentApplicationServiceRunner",
    "AssessmentContentFingerprint",
    "AssessmentEquivalenceResult",
    "AssessmentSemanticComparator",
    "CandidateManifestSelectiveScanService",
    "CandidateRepositoryState",
    "ChangeClassifier",
    "CompatibilityEvaluator",
    "CompatibilityResult",
    "CompleteAssessmentArtifacts",
    "DefaultRuleScopeProvider",
    "EngineCompatibilityFingerprint",
    "ExplanationFilters",
    "FileChange",
    "FileChangeDimensions",
    "FileChangeKind",
    "FileIncrementalExecutionRecordStore",
    "ImpactAnalysis",
    "ImpactAnalyzer",
    "InMemoryIncrementalExecutionRecordStore",
    "IncrementalAssessmentExecutor",
    "IncrementalAssessmentPlan",
    "IncrementalArtifactMergeError",
    "IncrementalArtifactMerger",
    "IncrementalBaseEligibility",
    "IncrementalCompatibilityError",
    "IncrementalConfigurationError",
    "IncrementalDependencyError",
    "IncrementalEligibilityError",
    "IncrementalEquivalenceError",
    "IncrementalExecutionError",
    "IncrementalExecutionMetrics",
    "IncrementalExecutionMode",
    "IncrementalExecutionPolicy",
    "IncrementalExecutionRecord",
    "IncrementalExecutionRecordNotFoundError",
    "IncrementalExecutionRequest",
    "IncrementalExecutionResult",
    "IncrementalExecutionStatus",
    "IncrementalExplainabilityService",
    "IncrementalExplanation",
    "IncrementalExplanationError",
    "IncrementalExplanationKind",
    "IncrementalFallbackError",
    "IncrementalGraphMergeError",
    "IncrementalInspectionError",
    "IncrementalInspectionService",
    "IncrementalManifestError",
    "IncrementalMergeValidationError",
    "IncrementalMergeValidator",
    "IncrementalMetricsCalculator",
    "IncrementalMetricsError",
    "IncrementalOperationsService",
    "IncrementalPlanMode",
    "IncrementalPlanRejectedError",
    "IncrementalPlanStep",
    "IncrementalPlanner",
    "IncrementalPlanningError",
    "IncrementalPlanningPolicy",
    "IncrementalPlanningRequest",
    "IncrementalPlanningService",
    "IncrementalRecomputeCounts",
    "IncrementalRecommendationError",
    "IncrementalRecommendationExecutor",
    "IncrementalReuseCounts",
    "IncrementalRolloutDisabledError",
    "IncrementalRolloutMode",
    "IncrementalRolloutPolicy",
    "IncrementalRuleExecutionError",
    "IncrementalRuleExecutor",
    "IncrementalStepType",
    "IncrementalValidationCheck",
    "IncrementalValidationCheckKind",
    "IncrementalValidationError",
    "IncrementalValidationIssue",
    "IncrementalValidationRequest",
    "IncrementalValidationResult",
    "IncrementalValidationService",
    "IncrementalValidationStatus",
    "MergedAssessmentPackage",
    "PlanningFileFingerprint",
    "PreviousRunEligibilityChecker",
    "RepositoryChangeSet",
    "ReuseAssessment",
    "ReuseDecision",
    "ReusePolicy",
    "SelectiveScanError",
    "SelectiveScanRequest",
    "SelectiveScanResult",
    "UnsupportedSelectiveScanService",
    "assessment_content_fingerprint",
    "create_incremental_assessment_executor",
    "create_incremental_operations_service",
    "create_incremental_planning_service",
    "current_engine_fingerprint",
    "execution_policy_from_settings",
    "merge_graph_snapshots",
    "merge_inventory",
    "nodes_sourced_from_paths",
    "planning_file_fingerprint",
    "policy_from_settings",
    "resolve_rollout_mode",
    "rollout_policy_from_settings",
]
