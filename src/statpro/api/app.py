"""FastAPI adapter over the StatPro statistical core and document seam."""

from __future__ import annotations

import base64
import binascii
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictInt

from statpro.analyses.capability import nonnormal_process_capability, normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    ResponseObjective,
    analyze_automatic_fractional_factorial_2level,
    analyze_box_behnken,
    analyze_central_composite,
    analyze_fractional_factorial_2level,
    analyze_full_factorial_2level,
    analyze_plackett_burman,
    automatic_fractional_factorial_2level,
    box_behnken_design,
    central_composite_design,
    explore_box_behnken_surface,
    explore_central_composite_surface,
    fractional_factorial_2level,
    full_factorial_2level,
    optimize_full_factorial_desirability,
    plackett_burman_design,
)
from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed
from statpro.analyses.spc import (
    c_chart,
    cusum_chart,
    ewma_chart,
    g_chart,
    individuals_moving_range,
    laney_p_prime,
    laney_u_prime,
    np_chart,
    p_chart,
    t_chart,
    u_chart,
    xbar_r,
    xbar_s,
)
from statpro.application.approval import (
    ApprovalAuthenticationError,
    ApprovalAuthorizationError,
    ApprovalConfigurationError,
    LocalApprovalAuthenticator,
)
from statpro.application.documents import (
    AtomicJsonDocumentRepository,
    DocumentConflictError,
    DocumentNotFoundError,
    DocumentRepository,
    DocumentStoreError,
    InvalidDocumentKeyError,
    StoredDocument,
)
from statpro.application.reports import (
    build_doe_report,
    export_doe_report_zip,
    render_doe_report_html,
)
from statpro.dmaic import (
    DmaicCharter,
    DmaicInputError,
    DmaicProject,
    DmaicVoiceOfCustomerStudy,
    create_project,
    save_charter,
    save_voice_of_customer,
)
from statpro.domain.data import (
    DatasetSnapshot,
    DataType,
    WorksheetSnapshot,
    create_worksheet,
    import_csv_bytes,
    replace_worksheet_cell,
)
from statpro.domain.errors import AnalysisInputError, DomainInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ResultBundle
from statpro.domain.schema import result_bundle_schema
from statpro.fmea import (
    ActionPriorityEntry,
    ActionPriorityPolicy,
    AnalysisEvidenceRef,
    ApprovalSignature,
    CharacteristicType,
    ControlPlanPhase,
    FmeaInputError,
    FmeaStudySnapshot,
    RiskRatings,
    StudyType,
    add_control_plan_item,
    add_failure_analysis,
    add_process_characteristic,
    add_process_step,
    add_recommended_action,
    approve_study,
    attach_action_priority_policy,
    build_study_report,
    complete_action,
    create_fmea_study,
    link_control_plan_analysis_evidence,
    submit_for_review,
)
from statpro.version import ENGINE_VERSION

ANALYSIS_RUNS = "analysis-runs"
DATASETS = "datasets"
WORKSHEETS = "worksheets"
FMEA_STUDIES = "fmea-studies"
FMEA_AP_POLICIES = "fmea-action-priority-policies"
DMAIC_PROJECTS = "dmaic-projects"
DMAIC_CHARTERS = "dmaic-charters"
DMAIC_VOICE_OF_CUSTOMER_STUDIES = "dmaic-voice-of-customer-studies"
RunId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImrRunRequest(ApiModel):
    run_id: RunId
    values: list[float]
    target: float | None = None
    sigma: float | None = None
    stage: Literal["phase_1", "phase_2"] = "phase_1"
    rules: Literal["basic", "western_electric", "nelson"] = "western_electric"


class XbarRRunRequest(ApiModel):
    run_id: RunId
    subgroups: list[list[float]]
    rules: Literal["basic", "nelson"] = "basic"


class EwmaRunRequest(ApiModel):
    run_id: RunId
    values: list[float]
    target: float | None = None
    sigma: float | None = None
    stage: Literal["phase_1", "phase_2"] = "phase_1"
    weight: float = 0.2
    limit_width: float = 3.0


class CusumRunRequest(ApiModel):
    run_id: RunId
    values: list[float]
    target: float | None = None
    sigma: float | None = None
    stage: Literal["phase_1", "phase_2"] = "phase_1"
    reference_value: float = 0.5
    decision_interval: float = 4.0


class AttributeChartRunRequest(ApiModel):
    run_id: RunId
    nonconforming: list[StrictInt]
    sample_sizes: list[StrictInt]


class CChartRunRequest(ApiModel):
    run_id: RunId
    defects: list[StrictInt]
    inspection_units: list[float] | None = None


class UChartRunRequest(ApiModel):
    run_id: RunId
    defects: list[StrictInt]
    inspection_units: list[float]


class GChartRunRequest(ApiModel):
    run_id: RunId
    opportunities_between_events: list[StrictInt]
    alpha: float = Field(default=0.005, gt=0.0, lt=0.5)


class TChartRunRequest(ApiModel):
    run_id: RunId
    time_between_events: list[float]
    alpha: float = Field(default=0.005, gt=0.0, lt=0.5)


class CapabilityRunRequest(ApiModel):
    run_id: RunId
    values: list[float]
    lsl: float | None = None
    usl: float | None = None
    target: float | None = None


class FactorRequest(ApiModel):
    name: str
    low: float
    high: float


class FullFactorialRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest]
    replicates: int = 1
    center_points: int = 0
    blocks: Literal[1, 2, 4, 8, 16] = 1
    randomize: bool = True
    seed: int = 0


class GeneratorRequest(ApiModel):
    factor: str
    terms: list[str] = Field(min_length=2)


class FractionalFactorialRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest]
    generators: list[GeneratorRequest] = Field(min_length=1, max_length=8)
    block_generators: list[list[str]] = Field(default_factory=list, max_length=4)
    replicates: int = 1
    foldover: bool = False
    foldover_factor: str | None = None
    randomize: bool = True
    seed: int = 0


class FractionalFactorialAnalysisRunRequest(FractionalFactorialRunRequest):
    responses: list[float]
    response_name: str = "Response"
    alpha: float = Field(default=0.05, ge=0.001, le=0.5)


class AutomaticFractionalFactorialRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest] = Field(min_length=3, max_length=10)
    runs: StrictInt | None = Field(default=None, ge=4, le=512)
    minimum_resolution: StrictInt = Field(default=3, ge=3, le=10)
    block_generators: list[list[str]] = Field(default_factory=list, max_length=4)
    replicates: StrictInt = Field(default=1, ge=1)
    foldover: bool = False
    foldover_factor: str | None = None
    randomize: bool = True
    seed: int = 0


class AutomaticFractionalFactorialAnalysisRunRequest(
    AutomaticFractionalFactorialRunRequest
):
    responses: list[float]
    response_name: str = "Response"
    alpha: float = Field(default=0.05, ge=0.001, le=0.5)


class PlackettBurmanRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest] = Field(min_length=2, max_length=47)
    runs: Literal[12, 20, 24, 28, 32, 36, 40, 44, 48] | None = None
    replicates: int = 1
    center_points: int = 0
    randomize: bool = True
    seed: int = 0


class PlackettBurmanAnalysisRunRequest(PlackettBurmanRunRequest):
    responses: list[float]
    response_name: str = "Response"
    alpha: float = Field(default=0.05, ge=0.001, le=0.5)


class FullFactorialAnalysisRunRequest(FullFactorialRunRequest):
    responses: list[float]
    response_name: str = "Response"
    interaction_order: int = Field(default=2, ge=1)
    prediction_points: list[dict[str, float]] = Field(default_factory=list, max_length=100)
    optimization_goal: Literal["maximize", "minimize"] | None = None


class CentralCompositeRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest] = Field(min_length=2, max_length=6)
    design_type: Literal["rotatable", "face_centered"] = "rotatable"
    center_points: int = Field(default=5, ge=1)
    replicates: int = Field(default=1, ge=1)
    randomize: bool = True
    seed: int = 0


class BoxBehnkenRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest] = Field(min_length=3, max_length=5)
    center_points: int | None = Field(default=None, ge=1)
    replicates: int = Field(default=1, ge=1)
    randomize: bool = True
    seed: int = 0


class BoxBehnkenAnalysisRunRequest(BoxBehnkenRunRequest):
    responses: list[float]
    response_name: str = "Response"
    alpha: float = Field(default=0.05, ge=0.001, le=0.5)


class BoxBehnkenSurfaceRunRequest(BoxBehnkenAnalysisRunRequest):
    plot_factors: list[str] | None = Field(default=None, min_length=2, max_length=2)
    hold_values: dict[str, float] = Field(default_factory=dict)
    grid_size: int = Field(default=21, ge=5, le=51)
    contour_levels: int = Field(default=7, ge=1, le=12)


class CentralCompositeAnalysisRunRequest(CentralCompositeRunRequest):
    responses: list[float]
    response_name: str = "Response"
    alpha: float = Field(default=0.05, ge=0.001, le=0.5)


class CentralCompositeSurfaceRunRequest(CentralCompositeAnalysisRunRequest):
    plot_factors: list[str] | None = Field(default=None, min_length=2, max_length=2)
    hold_values: dict[str, float] = Field(default_factory=dict)
    grid_size: int = Field(default=21, ge=5, le=51)
    contour_levels: int = Field(default=7, ge=1, le=12)


class ResponseObjectiveRequest(ApiModel):
    name: str
    responses: list[float]
    goal: Literal["maximize", "minimize", "target"]
    target: float
    lower: float | None = None
    upper: float | None = None
    weight: float = 1.0
    importance: float = 1.0


class FactorConstraintRequest(ApiModel):
    lower: float
    upper: float


class FullFactorialOptimizerRunRequest(FullFactorialRunRequest):
    objectives: list[ResponseObjectiveRequest] = Field(min_length=1, max_length=10)
    interaction_order: int = Field(default=2, ge=1)
    factor_constraints: dict[str, FactorConstraintRequest] = Field(default_factory=dict)


class MeasurementRequest(ApiModel):
    part: str
    operator: str
    measurement: float


class GageRrRunRequest(ApiModel):
    run_id: RunId
    records: list[MeasurementRequest]
    study_variation_multiplier: float = 6.0


class StoredRunResponse(ApiModel):
    run_id: str
    storage_version: int
    etag: str
    result: dict[str, Any]


class DoeReportRunResponse(ApiModel):
    run_id: str
    storage_version: int
    etag: str


class DoeReportAnalysisResponse(ApiModel):
    analysis_type: str
    engine_version: str
    input_digest: str
    result_digest: str


class DoeReportTableResponse(ApiModel):
    name: str
    columns: list[str]
    row_count: int
    rows: list[dict[str, Any]]


class DoeAnalysisReportResponse(ApiModel):
    report_type: str
    run: DoeReportRunResponse
    analysis: DoeReportAnalysisResponse
    parameters: dict[str, Any]
    diagnostics: dict[str, Any]
    tables: list[DoeReportTableResponse]
    plots: dict[str, Any]
    figures: list[dict[str, str]]
    template: dict[str, Any]
    assumptions: list[str]
    warnings: list[str]
    provenance: list[dict[str, Any]]
    limitations: list[str]
    report_digest: str


class RiskRatingsRequest(ApiModel):
    severity: int = Field(ge=1, le=10)
    occurrence: int = Field(ge=1, le=10)
    detection: int = Field(ge=1, le=10)


class CreateFmeaStudyRequest(ApiModel):
    study_id: RunId
    name: str
    study_type: StudyType
    standard_version: str
    actor: str
    occurred_at: str


class AddFailureAnalysisRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    item_id: RunId
    structure_element: str
    function: str
    requirement: str
    failure_mode: str
    effect: str
    cause: str
    prevention_control: str
    detection_control: str
    ratings: RiskRatingsRequest
    process_step_id: RunId | None = None
    characteristic_ids: list[RunId] = Field(default_factory=list)
    actor: str
    occurred_at: str


class AddProcessStepRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    step_id: RunId
    sequence: StrictInt = Field(ge=1)
    name: str
    operation: str
    actor: str
    occurred_at: str


class AddProcessCharacteristicRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    characteristic_id: RunId
    process_step_id: RunId
    name: str
    characteristic_type: CharacteristicType
    specification: str
    special_classification: str | None = None
    actor: str
    occurred_at: str


class AddControlPlanItemRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    control_id: RunId
    phase: ControlPlanPhase
    characteristic_id: RunId
    failure_item_ids: list[RunId] = Field(min_length=1)
    measurement_method: str
    sample_size: StrictInt = Field(ge=1)
    frequency: str
    control_method: str
    reaction_plan: str
    reaction_owner: str
    actor: str
    occurred_at: str


class LinkControlPlanAnalysisEvidenceRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    run_id: RunId
    actor: str
    occurred_at: str


class ActionPriorityEntryRequest(ApiModel):
    severity: StrictInt = Field(ge=1, le=10)
    occurrence: StrictInt = Field(ge=1, le=10)
    detection: StrictInt = Field(ge=1, le=10)
    priority: str = Field(min_length=1, max_length=32)


class CreateActionPriorityPolicyRequest(ApiModel):
    policy_id: RunId
    standard_version: str = Field(min_length=1, max_length=128)
    entries: list[ActionPriorityEntryRequest] = Field(min_length=1, max_length=1000)


class AddRecommendedActionRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    action_id: RunId
    item_id: RunId
    description: str
    owner: str
    due_date: str
    actor: str
    occurred_at: str


class CompleteRecommendedActionRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    result: str
    evidence_refs: list[str] = Field(default_factory=list)
    revised_ratings: RiskRatingsRequest
    actor: str
    occurred_at: str


class FmeaTransitionRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    actor: str
    occurred_at: str


class ApproveFmeaStudyRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    user_id: RunId
    password: SecretStr = Field(min_length=1, max_length=1024)
    meaning: Literal["approval"] = "approval"


class AttachActionPriorityPolicyRequest(FmeaTransitionRequest):
    policy_key: RunId


class StoredFmeaStudyResponse(ApiModel):
    study_id: str
    storage_version: int
    etag: str
    study: dict[str, Any]


class CreateDmaicProjectRequest(ApiModel):
    project_id: RunId
    title: str
    owner_ref: str
    sponsor_ref: str | None = None
    champion_ref: str | None = None
    department: str | None = None
    start_date: str | None = None
    target_end_date: str | None = None


class SaveDmaicCharterRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    business_case: str
    problem_statement: str
    scope_in: list[str] = Field(min_length=1)
    scope_out: list[str] = Field(min_length=1)
    success_metrics: list[str] = Field(min_length=1)
    team_refs: list[str] = Field(min_length=1)
    budget: str | None = None
    milestones: list[str] = Field(min_length=1)
    risk_refs: list[str] = Field(min_length=1)
    assumptions_constraints: list[str] = Field(min_length=1)
    actor: str
    occurred_at: str


class SaveDmaicVoiceOfCustomerRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    collection_plan: str
    data_points: list[str] = Field(min_length=1)
    requirements: list[str] = Field(min_length=1)
    pain_points: list[str] = Field(min_length=1)
    opportunities: list[str] = Field(min_length=1)
    actions: list[str] = Field(min_length=1)
    recommendations: list[str] = Field(min_length=1)
    next_steps: list[str] = Field(min_length=1)
    actor: str
    occurred_at: str


class StoredDmaicProjectResponse(ApiModel):
    project_id: str
    storage_version: int
    etag: str
    project: dict[str, Any]


class StoredDmaicCharterResponse(ApiModel):
    document_id: str
    storage_version: int
    etag: str
    charter: dict[str, Any]


class StoredDmaicVoiceOfCustomerResponse(ApiModel):
    document_id: str
    storage_version: int
    etag: str
    study: dict[str, Any]


class StoredActionPriorityPolicyResponse(ApiModel):
    policy_key: str
    storage_version: int
    etag: str
    policy: dict[str, Any]


class ImportCsvWorksheetRequest(ApiModel):
    file_name: str = Field(min_length=1, max_length=255)
    worksheet_name: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1, max_length=28_000_000)
    type_hints: dict[str, DataType] = Field(default_factory=dict)
    missing_tokens: list[str] = Field(default_factory=lambda: [""])


class ReplaceWorksheetCellRequest(ApiModel):
    expected_storage_version: int = Field(ge=1)
    row_index: int = Field(ge=0)
    column_name: str = Field(min_length=1)
    value: str | float | bool | None


class StoredWorksheetResponse(ApiModel):
    worksheet_id: str
    storage_version: int
    etag: str
    worksheet: dict[str, Any]
    dataset: dict[str, Any] | None = None


def _response(stored: StoredDocument) -> StoredRunResponse:
    return StoredRunResponse(
        run_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        result=stored.document["result"],
    )


def _fmea_response(stored: StoredDocument) -> StoredFmeaStudyResponse:
    study = _deserialize_fmea_study(stored)
    return StoredFmeaStudyResponse(
        study_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        study=study.to_dict(),
    )


def _deserialize_action_priority_policy(stored: StoredDocument) -> ActionPriorityPolicy:
    try:
        return ActionPriorityPolicy.from_dict(stored.document["policy"])
    except (KeyError, TypeError, ValueError, FmeaInputError) as error:
        raise DocumentStoreError(
            f"Stored Action Priority policy {stored.key} does not match its owned format."
        ) from error


def _action_priority_policy_response(
    stored: StoredDocument,
) -> StoredActionPriorityPolicyResponse:
    policy = _deserialize_action_priority_policy(stored)
    return StoredActionPriorityPolicyResponse(
        policy_key=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        policy=policy.to_dict(),
    )


def _load_action_priority_policy(
    repository: DocumentRepository, policy_key: str
) -> tuple[StoredDocument, ActionPriorityPolicy]:
    stored = repository.load(FMEA_AP_POLICIES, policy_key)
    policy = _deserialize_action_priority_policy(stored)
    if policy.policy_key != stored.key:
        raise DocumentStoreError(
            f"Stored Action Priority policy {stored.key} has a mismatched identity."
        )
    return stored, policy


def _load_attached_action_priority_policy(
    repository: DocumentRepository, study: FmeaStudySnapshot
) -> ActionPriorityPolicy | None:
    if study.action_priority_policy_digest is None:
        if (
            study.action_priority_policy_id is not None
            or study.action_priority_policy_key is not None
        ):
            raise DocumentStoreError(
                "FMEA Study has an incomplete Action Priority policy identity."
            )
        return None
    if study.action_priority_policy_key is None:
        raise DocumentStoreError(
            "Attached Action Priority policy has no lookup key; reattach an imported policy."
        )
    _stored, policy = _load_action_priority_policy(
        repository, study.action_priority_policy_key
    )
    if (
        policy.policy_id != study.action_priority_policy_id
        or policy.digest != study.action_priority_policy_digest
    ):
        raise DocumentStoreError(
            "Attached Action Priority policy identity does not match the FMEA Study."
        )
    return policy


def _deserialize_fmea_study(stored: StoredDocument) -> FmeaStudySnapshot:
    try:
        return FmeaStudySnapshot.from_dict(stored.document["study"])
    except (KeyError, TypeError, ValueError) as error:
        raise DocumentStoreError(
            f"Stored FMEA study {stored.key} does not match its owned format."
        ) from error


def _load_fmea_study(repository: DocumentRepository, study_id: str) -> tuple[StoredDocument, FmeaStudySnapshot]:
    stored = repository.load(FMEA_STUDIES, study_id)
    study = _deserialize_fmea_study(stored)
    return stored, study


def _save_fmea_study(
    repository: DocumentRepository,
    study: FmeaStudySnapshot,
    *,
    expected_version: int,
) -> StoredDocument:
    return repository.save(
        FMEA_STUDIES,
        study.study_id,
        {"kind": "fmea_study", "study_id": study.study_id, "study": study.to_dict()},
        expected_version=expected_version,
    )


def _deserialize_dmaic_project(stored: StoredDocument) -> DmaicProject:
    try:
        return DmaicProject.from_dict(stored.document["project"])
    except (KeyError, TypeError, ValueError, DmaicInputError) as error:
        raise DocumentStoreError(
            f"Stored DMAIC project {stored.key} does not match its owned format."
        ) from error


def _deserialize_dmaic_charter(stored: StoredDocument) -> DmaicCharter:
    try:
        return DmaicCharter.from_dict(stored.document["charter"])
    except (KeyError, TypeError, ValueError, DmaicInputError) as error:
        raise DocumentStoreError(
            f"Stored DMAIC charter {stored.key} does not match its owned format."
        ) from error


def _deserialize_dmaic_voice_of_customer(
    stored: StoredDocument,
) -> DmaicVoiceOfCustomerStudy:
    try:
        return DmaicVoiceOfCustomerStudy.from_dict(stored.document["study"])
    except (KeyError, TypeError, ValueError, DmaicInputError) as error:
        raise DocumentStoreError(
            f"Stored DMAIC Voice of Customer study {stored.key} does not match its owned format."
        ) from error


def _dmaic_project_response(stored: StoredDocument) -> StoredDmaicProjectResponse:
    project = _deserialize_dmaic_project(stored)
    return StoredDmaicProjectResponse(
        project_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        project=project.to_dict(),
    )


def _dmaic_charter_response(stored: StoredDocument) -> StoredDmaicCharterResponse:
    charter = _deserialize_dmaic_charter(stored)
    return StoredDmaicCharterResponse(
        document_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        charter=charter.to_dict(),
    )


def _dmaic_voice_of_customer_response(
    stored: StoredDocument,
) -> StoredDmaicVoiceOfCustomerResponse:
    study = _deserialize_dmaic_voice_of_customer(stored)
    return StoredDmaicVoiceOfCustomerResponse(
        document_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        study=study.to_dict(),
    )


def _load_dmaic_project(
    repository: DocumentRepository, project_id: str
) -> tuple[StoredDocument, DmaicProject]:
    stored = repository.load(DMAIC_PROJECTS, project_id)
    return stored, _deserialize_dmaic_project(stored)


def _save_dmaic_project(
    repository: DocumentRepository, project: DmaicProject, *, expected_version: int
) -> StoredDocument:
    return repository.save(
        DMAIC_PROJECTS,
        project.project_id,
        {"kind": "dmaic_project", "project_id": project.project_id, "project": project.to_dict()},
        expected_version=expected_version,
    )


def _save_dmaic_charter(
    repository: DocumentRepository, charter: DmaicCharter
) -> StoredDocument:
    return repository.save(
        DMAIC_CHARTERS,
        charter.document_id,
        {"kind": "dmaic_project_charter", "document_id": charter.document_id, "charter": charter.to_dict()},
        expected_version=0,
    )


def _save_dmaic_voice_of_customer(
    repository: DocumentRepository, study: DmaicVoiceOfCustomerStudy
) -> StoredDocument:
    return repository.save(
        DMAIC_VOICE_OF_CUSTOMER_STUDIES,
        study.document_id,
        {
            "kind": "dmaic_voice_of_customer_study",
            "document_id": study.document_id,
            "study": study.to_dict(),
        },
        expected_version=0,
    )


def _worksheet_response(
    stored: StoredDocument,
    *,
    dataset: DatasetSnapshot | None = None,
) -> StoredWorksheetResponse:
    return StoredWorksheetResponse(
        worksheet_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        worksheet=stored.document["worksheet"],
        dataset=None if dataset is None else dataset.to_dict(),
    )


def _load_worksheet(
    repository: DocumentRepository, worksheet_id: str
) -> tuple[StoredDocument, WorksheetSnapshot]:
    stored = repository.load(WORKSHEETS, worksheet_id)
    try:
        worksheet = WorksheetSnapshot.from_dict(stored.document["worksheet"])
    except (KeyError, TypeError, ValueError) as error:
        raise DocumentStoreError(
            f"Stored worksheet {worksheet_id} does not match its owned format."
        ) from error
    return stored, worksheet


def _save_worksheet(
    repository: DocumentRepository,
    worksheet: WorksheetSnapshot,
    *,
    expected_version: int,
) -> StoredDocument:
    return repository.save(
        WORKSHEETS,
        worksheet.worksheet_id,
        {
            "kind": "worksheet",
            "worksheet_id": worksheet.worksheet_id,
            "worksheet": worksheet.to_dict(),
        },
        expected_version=expected_version,
    )


def _ensure_dataset(
    repository: DocumentRepository, dataset: DatasetSnapshot
) -> StoredDocument:
    document = {
        "kind": "dataset",
        "dataset_id": dataset.dataset_id,
        "dataset": dataset.to_dict(),
    }
    try:
        stored = repository.load(DATASETS, dataset.dataset_id)
    except DocumentNotFoundError:
        return repository.save(DATASETS, dataset.dataset_id, document, expected_version=0)
    if stored.document != document:
        raise DocumentStoreError(
            f"Stored Dataset {dataset.dataset_id} conflicts with its content identity."
        )
    return stored


def _save_run(
    repository: DocumentRepository, run_id: str, result: ResultBundle
) -> StoredDocument:
    return repository.save(
        ANALYSIS_RUNS,
        run_id,
        {
            "kind": "analysis_run",
            "run_id": run_id,
            "result": result.to_dict(),
        },
        expected_version=0,
    )


def _load_analysis_evidence_reference(
    repository: DocumentRepository, run_id: str
) -> AnalysisEvidenceRef:
    """Parse a stored Run's owned identity once for linking and report checks."""

    stored = repository.load(ANALYSIS_RUNS, run_id)
    result = stored.document.get("result")
    if (
        stored.key != run_id
        or stored.document.get("kind") != "analysis_run"
        or stored.document.get("run_id") != run_id
        or not isinstance(result, dict)
        or not isinstance(result.get("analysis_type"), str)
        or not result["analysis_type"]
        or not isinstance(result.get("input_digest"), str)
        or re.fullmatch(r"[0-9a-f]{64}", result["input_digest"]) is None
    ):
        raise DocumentStoreError("Stored analysis Run has an invalid owned format.")
    return AnalysisEvidenceRef(
        run_id=run_id,
        analysis_type=result["analysis_type"],
        run_etag=stored.etag,
        input_digest=result["input_digest"],
    )


def _check_fmea_analysis_evidence(
    repository: DocumentRepository, study: FmeaStudySnapshot
) -> list[dict[str, str]]:
    """Report each reference without treating missing or unreadable Runs as verified."""

    checks: list[dict[str, str]] = []
    observed: dict[str, AnalysisEvidenceRef | str] = {}
    for control in study.control_plan_items:
        for reference in control.analysis_evidence:
            if reference.run_id not in observed:
                try:
                    observed[reference.run_id] = _load_analysis_evidence_reference(
                        repository, reference.run_id
                    )
                except DocumentNotFoundError:
                    observed[reference.run_id] = "missing"
                except DocumentStoreError:
                    observed[reference.run_id] = "unavailable"
            current = observed[reference.run_id]
            checks.append({
                "control_id": control.control_id,
                "run_id": reference.run_id,
                "status": (
                    current if isinstance(current, str)
                    else "verified" if current == reference else "mismatch"
                ),
            })
    return checks


def create_app(
    repository: DocumentRepository,
    approval_authenticator: LocalApprovalAuthenticator | None = None,
) -> FastAPI:
    """Create a testable local API with an injected persistence adapter."""

    app = FastAPI(
        title="StatPro Local API",
        version=ENGINE_VERSION,
        docs_url="/docs",
        redoc_url=None,
    )

    @app.exception_handler(DomainInputError)
    async def domain_error_handler(_request: object, error: DomainInputError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"ok": False, "error": error.to_dict()})

    @app.exception_handler(ApprovalAuthenticationError)
    async def approval_authentication_handler(
        _request: object, _error: ApprovalAuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": {
                "code": "approval_authentication_failed",
                "message": "Approval credentials are invalid.",
            }},
        )

    @app.exception_handler(ApprovalAuthorizationError)
    async def approval_authorization_handler(
        _request: object, error: ApprovalAuthorizationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"ok": False, "error": {
                "code": "approval_not_authorized", "message": str(error),
            }},
        )

    @app.exception_handler(ApprovalConfigurationError)
    async def approval_configuration_handler(
        _request: object, error: ApprovalConfigurationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": {
                "code": "approval_authentication_unavailable", "message": str(error),
            }},
        )

    @app.exception_handler(RequestValidationError)
    async def request_error_handler(
        _request: object, error: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                key: value
                for key, value in issue.items()
                if key in {"type", "loc", "msg"}
            }
            for issue in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": {
                    "code": "invalid_request",
                    "message": "Request does not match the declared contract.",
                    "details": jsonable_encoder(details),
                },
            },
        )

    @app.exception_handler(DocumentNotFoundError)
    async def not_found_handler(_request: object, error: DocumentNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "error": {"code": "not_found", "message": str(error)}},
        )

    @app.exception_handler(DocumentConflictError)
    async def conflict_handler(_request: object, error: DocumentConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"ok": False, "error": {"code": "storage_conflict", "message": str(error)}},
        )

    @app.exception_handler(InvalidDocumentKeyError)
    async def key_error_handler(_request: object, error: InvalidDocumentKeyError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"ok": False, "error": {"code": "invalid_identifier", "message": str(error)}},
        )

    @app.exception_handler(DocumentStoreError)
    async def store_error_handler(_request: object, _error: DocumentStoreError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": {
                    "code": "storage_failure",
                    "message": "The local document store could not complete the request.",
                },
            },
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True, "engine_version": ENGINE_VERSION, "local_only": True}

    @app.get("/v1/schemas/result-bundle")
    def get_result_bundle_schema() -> dict[str, Any]:
        return result_bundle_schema()

    @app.post("/v1/analysis-runs/imr", status_code=201, response_model=StoredRunResponse)
    def run_imr(request: ImrRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            individuals_moving_range(
                request.values,
                target=request.target,
                sigma=request.sigma,
                stage=request.stage,
                rules=request.rules,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/xbar-r", status_code=201, response_model=StoredRunResponse)
    def run_xbar_r(request: XbarRRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            xbar_r(request.subgroups, rules=request.rules),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/xbar-s", status_code=201, response_model=StoredRunResponse)
    def run_xbar_s(request: XbarRRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            xbar_s(request.subgroups, rules=request.rules),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/ewma", status_code=201, response_model=StoredRunResponse)
    def run_ewma(request: EwmaRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            ewma_chart(
                request.values,
                target=request.target,
                sigma=request.sigma,
                stage=request.stage,
                weight=request.weight,
                limit_width=request.limit_width,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/cusum", status_code=201, response_model=StoredRunResponse)
    def run_cusum(request: CusumRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            cusum_chart(
                request.values,
                target=request.target,
                sigma=request.sigma,
                stage=request.stage,
                reference_value=request.reference_value,
                decision_interval=request.decision_interval,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/laney-p-prime", status_code=201, response_model=StoredRunResponse)
    def run_laney_p_prime(request: AttributeChartRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            laney_p_prime(request.nonconforming, request.sample_sizes),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/laney-u-prime", status_code=201, response_model=StoredRunResponse)
    def run_laney_u_prime(request: UChartRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            laney_u_prime(request.defects, request.inspection_units),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/p-chart", status_code=201, response_model=StoredRunResponse)
    def run_p_chart(
        request: AttributeChartRunRequest, response: Response
    ) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            p_chart(request.nonconforming, request.sample_sizes),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/np-chart", status_code=201, response_model=StoredRunResponse)
    def run_np_chart(
        request: AttributeChartRunRequest, response: Response
    ) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            np_chart(request.nonconforming, request.sample_sizes),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/c-chart", status_code=201, response_model=StoredRunResponse)
    def run_c_chart(request: CChartRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            c_chart(request.defects, request.inspection_units),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/u-chart", status_code=201, response_model=StoredRunResponse)
    def run_u_chart(request: UChartRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            u_chart(request.defects, request.inspection_units),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/g-chart", status_code=201, response_model=StoredRunResponse)
    def run_g_chart(request: GChartRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            g_chart(request.opportunities_between_events, alpha=request.alpha),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post("/v1/analysis-runs/t-chart", status_code=201, response_model=StoredRunResponse)
    def run_t_chart(request: TChartRunRequest, response: Response) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            t_chart(request.time_between_events, alpha=request.alpha),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/capability-normal",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_capability(
        request: CapabilityRunRequest, response: Response
    ) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            normal_process_capability(
                request.values, lsl=request.lsl, usl=request.usl, target=request.target
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/capability-nonnormal",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_nonnormal_capability(
        request: CapabilityRunRequest, response: Response
    ) -> StoredRunResponse:
        stored = _save_run(
            repository,
            request.run_id,
            nonnormal_process_capability(
                request.values, lsl=request.lsl, usl=request.usl, target=request.target
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-full-factorial",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_doe(request: FullFactorialRunRequest, response: Response) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            full_factorial_2level(
                factors,
                replicates=request.replicates,
                center_points=request.center_points,
                blocks=request.blocks,
                randomize=request.randomize,
                seed=request.seed,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-full-factorial-analysis",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def analyze_doe(
        request: FullFactorialAnalysisRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            analyze_full_factorial_2level(
                factors,
                request.responses,
                response_name=request.response_name,
                replicates=request.replicates,
                center_points=request.center_points,
                blocks=request.blocks,
                randomize=request.randomize,
                seed=request.seed,
                interaction_order=request.interaction_order,
                prediction_points=request.prediction_points,
                optimization_goal=request.optimization_goal,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-fractional-factorial",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_fractional_doe(
        request: FractionalFactorialRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        generators = [
            GeneratorDefinition(**generator.model_dump()) for generator in request.generators
        ]
        stored = _save_run(
            repository,
            request.run_id,
            fractional_factorial_2level(
                factors,
                generators,
                block_generators=request.block_generators,
                replicates=request.replicates,
                foldover=request.foldover,
                foldover_factor=request.foldover_factor,
                randomize=request.randomize,
                seed=request.seed,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-fractional-factorial-auto",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_automatic_fractional_doe(
        request: AutomaticFractionalFactorialRunRequest,
        response: Response,
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            automatic_fractional_factorial_2level(
                factors,
                runs=request.runs,
                minimum_resolution=request.minimum_resolution,
                block_generators=request.block_generators,
                replicates=request.replicates,
                foldover=request.foldover,
                foldover_factor=request.foldover_factor,
                randomize=request.randomize,
                seed=request.seed,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-box-behnken",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_box_behnken_doe(
        request: BoxBehnkenRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            box_behnken_design(
                factors,
                center_points=request.center_points,
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-box-behnken-analysis",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def analyze_box_behnken_doe(
        request: BoxBehnkenAnalysisRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            analyze_box_behnken(
                factors,
                request.responses,
                response_name=request.response_name,
                center_points=request.center_points,
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-box-behnken-surface",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def explore_box_behnken_doe_surface(
        request: BoxBehnkenSurfaceRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            explore_box_behnken_surface(
                factors,
                request.responses,
                response_name=request.response_name,
                center_points=request.center_points,
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
                plot_factors=request.plot_factors,
                hold_values=request.hold_values,
                grid_size=request.grid_size,
                contour_levels=request.contour_levels,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-central-composite",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_central_composite_doe(
        request: CentralCompositeRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            central_composite_design(
                factors,
                design_type=request.design_type,
                center_points=request.center_points,
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-central-composite-analysis",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def analyze_central_composite_doe(
        request: CentralCompositeAnalysisRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            analyze_central_composite(
                factors,
                request.responses,
                response_name=request.response_name,
                design_type=request.design_type,
                center_points=request.center_points,
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-central-composite-surface",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def explore_central_composite_doe_surface(
        request: CentralCompositeSurfaceRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            explore_central_composite_surface(
                factors,
                request.responses,
                response_name=request.response_name,
                design_type=request.design_type,
                center_points=request.center_points,
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
                plot_factors=request.plot_factors,
                hold_values=request.hold_values,
                grid_size=request.grid_size,
                contour_levels=request.contour_levels,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-fractional-factorial-analysis",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def analyze_fractional_doe(
        request: FractionalFactorialAnalysisRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        generators = [
            GeneratorDefinition(**generator.model_dump()) for generator in request.generators
        ]
        stored = _save_run(
            repository,
            request.run_id,
            analyze_fractional_factorial_2level(
                factors,
                generators,
                request.responses,
                response_name=request.response_name,
                block_generators=request.block_generators,
                replicates=request.replicates,
                foldover=request.foldover,
                foldover_factor=request.foldover_factor,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-fractional-factorial-auto-analysis",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def analyze_automatic_fractional_doe(
        request: AutomaticFractionalFactorialAnalysisRunRequest,
        response: Response,
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            analyze_automatic_fractional_factorial_2level(
                factors,
                request.responses,
                response_name=request.response_name,
                runs=request.runs,
                minimum_resolution=request.minimum_resolution,
                block_generators=request.block_generators,
                replicates=request.replicates,
                foldover=request.foldover,
                foldover_factor=request.foldover_factor,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-plackett-burman",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_plackett_burman_doe(
        request: PlackettBurmanRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            plackett_burman_design(
                factors,
                runs=request.runs,
                replicates=request.replicates,
                center_points=request.center_points,
                randomize=request.randomize,
                seed=request.seed,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-plackett-burman-analysis",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def analyze_plackett_burman_doe(
        request: PlackettBurmanAnalysisRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        stored = _save_run(
            repository,
            request.run_id,
            analyze_plackett_burman(
                factors,
                request.responses,
                response_name=request.response_name,
                runs=request.runs,
                replicates=request.replicates,
                center_points=request.center_points,
                randomize=request.randomize,
                seed=request.seed,
                alpha=request.alpha,
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/doe-response-optimizer",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def optimize_doe_responses(
        request: FullFactorialOptimizerRunRequest, response: Response
    ) -> StoredRunResponse:
        factors = [FactorDefinition(**factor.model_dump()) for factor in request.factors]
        objectives = [
            ResponseObjective(**objective.model_dump())
            for objective in request.objectives
        ]
        stored = _save_run(
            repository,
            request.run_id,
            optimize_full_factorial_desirability(
                factors,
                objectives,
                replicates=request.replicates,
                center_points=request.center_points,
                randomize=request.randomize,
                seed=request.seed,
                interaction_order=request.interaction_order,
                factor_constraints={
                    name: constraint.model_dump()
                    for name, constraint in request.factor_constraints.items()
                },
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.post(
        "/v1/analysis-runs/gage-rr-crossed",
        status_code=201,
        response_model=StoredRunResponse,
    )
    def run_gage_rr(request: GageRrRunRequest, response: Response) -> StoredRunResponse:
        records = [MeasurementRecord(**record.model_dump()) for record in request.records]
        stored = _save_run(
            repository,
            request.run_id,
            gage_rr_crossed(
                records, study_variation_multiplier=request.study_variation_multiplier
            ),
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.get("/v1/analysis-runs/{run_id}", response_model=StoredRunResponse)
    def get_run(run_id: RunId, response: Response) -> StoredRunResponse:
        stored = repository.load(ANALYSIS_RUNS, run_id)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _response(stored)

    @app.get(
        "/v1/analysis-runs/{run_id}/report",
        response_model=DoeAnalysisReportResponse,
    )
    def get_doe_report(
        run_id: RunId,
        response: Response,
        template_id: Annotated[str, Query(pattern=r"^(standard|customer_review|regulatory_review)$")] = "standard",
    ) -> dict[str, Any]:
        report = build_doe_report(repository.load(ANALYSIS_RUNS, run_id), template_id=template_id)
        response.headers["ETag"] = f'"{report["report_digest"]}"'
        return report

    @app.get("/v1/analysis-runs/{run_id}/report.html")
    def get_doe_report_html(
        run_id: RunId,
        template_id: Annotated[str, Query(pattern=r"^(standard|customer_review|regulatory_review)$")] = "standard",
    ) -> Response:
        report = build_doe_report(repository.load(ANALYSIS_RUNS, run_id), template_id=template_id)
        return Response(
            content=render_doe_report_html(report),
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{run_id}-doe-report.html"',
                "ETag": f'"{report["report_digest"]}"',
            },
        )

    @app.get("/v1/analysis-runs/{run_id}/export")
    def export_doe_report(
        run_id: RunId,
        template_id: Annotated[str, Query(pattern=r"^(standard|customer_review|regulatory_review)$")] = "standard",
    ) -> Response:
        report = build_doe_report(repository.load(ANALYSIS_RUNS, run_id), template_id=template_id)
        return Response(
            content=export_doe_report_zip(report),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{run_id}-doe-export.zip"',
                "ETag": f'"{report["report_digest"]}"',
            },
        )

    @app.get("/v1/analysis-runs")
    def list_runs(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        after: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")] = None,
    ) -> dict[str, Any]:
        stored = repository.list_documents(
            ANALYSIS_RUNS, after=after, limit=limit + 1
        )
        has_more = len(stored) > limit
        page = stored[:limit]
        return {
            "items": [_response(item).model_dump() for item in page],
            "next_after": page[-1].key if has_more and page else None,
        }

    @app.post(
        "/v1/worksheets/import-csv",
        status_code=201,
        response_model=StoredWorksheetResponse,
    )
    def import_worksheet_csv(
        request: ImportCsvWorksheetRequest, response: Response
    ) -> StoredWorksheetResponse:
        try:
            source_bytes = base64.b64decode(request.content_base64, validate=True)
        except (binascii.Error, ValueError) as error:
            raise AnalysisInputError(
                "invalid_base64", "CSV content is not valid base64.", "content_base64"
            ) from error
        if len(source_bytes) > 20_000_000:
            raise AnalysisInputError(
                "dataset_too_large",
                "CSV upload supports at most 20,000,000 bytes.",
                "content_base64",
            )
        dataset = import_csv_bytes(
            source_bytes,
            location=request.file_name,
            type_hints=request.type_hints,
            missing_tokens=request.missing_tokens,
        )
        _ensure_dataset(repository, dataset)
        worksheet = create_worksheet(dataset, name=request.worksheet_name)
        stored = _save_worksheet(repository, worksheet, expected_version=0)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _worksheet_response(stored, dataset=dataset)

    @app.get("/v1/worksheets")
    def list_worksheets(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        after: Annotated[
            str | None,
            Query(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"),
        ] = None,
    ) -> dict[str, Any]:
        stored = repository.list_documents(WORKSHEETS, after=after, limit=limit + 1)
        has_more = len(stored) > limit
        page = stored[:limit]
        return {
            "items": [_worksheet_response(item).model_dump() for item in page],
            "next_after": page[-1].key if has_more and page else None,
        }

    @app.get("/v1/worksheets/{worksheet_id}", response_model=StoredWorksheetResponse)
    def get_worksheet(
        worksheet_id: RunId, response: Response
    ) -> StoredWorksheetResponse:
        stored, _worksheet = _load_worksheet(repository, worksheet_id)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _worksheet_response(stored)

    @app.patch(
        "/v1/worksheets/{worksheet_id}/cells",
        response_model=StoredWorksheetResponse,
    )
    def replace_cell(
        worksheet_id: RunId,
        request: ReplaceWorksheetCellRequest,
        response: Response,
    ) -> StoredWorksheetResponse:
        _stored, worksheet = _load_worksheet(repository, worksheet_id)
        revised = replace_worksheet_cell(
            worksheet,
            row_index=request.row_index,
            column_name=request.column_name,
            value=request.value,
        )
        saved = _save_worksheet(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _worksheet_response(saved)

    @app.post(
        "/v1/fmea-action-priority-policies",
        status_code=201,
        response_model=StoredActionPriorityPolicyResponse,
    )
    def create_action_priority_policy(
        request: CreateActionPriorityPolicyRequest,
        response: Response,
    ) -> StoredActionPriorityPolicyResponse:
        policy = ActionPriorityPolicy(
            policy_id=request.policy_id,
            standard_version=request.standard_version,
            entries=tuple(
                ActionPriorityEntry(**entry.model_dump()) for entry in request.entries
            ),
        )
        stored = repository.save(
            FMEA_AP_POLICIES,
            policy.policy_key,
            {"kind": "fmea_action_priority_policy", "policy": policy.to_dict()},
            expected_version=0,
        )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _action_priority_policy_response(stored)

    @app.get("/v1/fmea-action-priority-policies")
    def list_action_priority_policies(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        after: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")] = None,
    ) -> dict[str, Any]:
        stored = repository.list_documents(
            FMEA_AP_POLICIES, after=after, limit=limit + 1
        )
        has_more = len(stored) > limit
        page = stored[:limit]
        return {
            "items": [
                _action_priority_policy_response(item).model_dump() for item in page
            ],
            "next_after": page[-1].key if has_more and page else None,
        }

    @app.get(
        "/v1/fmea-action-priority-policies/{policy_key}",
        response_model=StoredActionPriorityPolicyResponse,
    )
    def get_action_priority_policy(
        policy_key: RunId, response: Response
    ) -> StoredActionPriorityPolicyResponse:
        stored, _policy = _load_action_priority_policy(repository, policy_key)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _action_priority_policy_response(stored)

    @app.post("/v1/dmaic-projects", status_code=201, response_model=StoredDmaicProjectResponse)
    def create_dmaic_project(
        request: CreateDmaicProjectRequest, response: Response
    ) -> StoredDmaicProjectResponse:
        project = create_project(**request.model_dump())
        stored = _save_dmaic_project(repository, project, expected_version=0)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _dmaic_project_response(stored)

    @app.get("/v1/dmaic-projects")
    def list_dmaic_projects(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        after: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")] = None,
    ) -> dict[str, Any]:
        stored = repository.list_documents(DMAIC_PROJECTS, after=after, limit=limit + 1)
        has_more = len(stored) > limit
        page = stored[:limit]
        return {
            "items": [_dmaic_project_response(item).model_dump() for item in page],
            "next_after": page[-1].key if has_more and page else None,
        }

    @app.get("/v1/dmaic-projects/{project_id}", response_model=StoredDmaicProjectResponse)
    def get_dmaic_project(project_id: RunId, response: Response) -> StoredDmaicProjectResponse:
        stored, _project = _load_dmaic_project(repository, project_id)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _dmaic_project_response(stored)

    @app.post(
        "/v1/dmaic-projects/{project_id}/charters",
        status_code=201,
        response_model=StoredDmaicProjectResponse,
    )
    def create_dmaic_charter(
        project_id: RunId, request: SaveDmaicCharterRequest, response: Response
    ) -> StoredDmaicProjectResponse:
        stored, project = _load_dmaic_project(repository, project_id)
        if stored.storage_version != request.expected_storage_version:
            raise DocumentConflictError(
                f"Expected storage version {request.expected_storage_version}; found {stored.storage_version}."
            )
        revised, charter = save_charter(
            project,
            business_case=request.business_case,
            problem_statement=request.problem_statement,
            scope_in=tuple(request.scope_in),
            scope_out=tuple(request.scope_out),
            success_metrics=tuple(request.success_metrics),
            team_refs=tuple(request.team_refs),
            budget=request.budget,
            milestones=tuple(request.milestones),
            risk_refs=tuple(request.risk_refs),
            assumptions_constraints=tuple(request.assumptions_constraints),
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        _save_dmaic_charter(repository, charter)
        saved = _save_dmaic_project(
            repository, revised, expected_version=request.expected_storage_version
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _dmaic_project_response(saved)

    @app.get(
        "/v1/dmaic-projects/{project_id}/charters/{document_id}",
        response_model=StoredDmaicCharterResponse,
    )
    def get_dmaic_charter(
        project_id: RunId, document_id: RunId, response: Response
    ) -> StoredDmaicCharterResponse:
        _stored_project, project = _load_dmaic_project(repository, project_id)
        stored = repository.load(DMAIC_CHARTERS, document_id)
        charter = _deserialize_dmaic_charter(stored)
        if charter.project_id != project.project_id:
            raise DocumentNotFoundError(f"Document {DMAIC_CHARTERS}/{document_id} does not exist.")
        response.headers["ETag"] = f'"{stored.etag}"'
        return _dmaic_charter_response(stored)

    @app.post(
        "/v1/dmaic-projects/{project_id}/voice-of-customer-studies",
        status_code=201,
        response_model=StoredDmaicProjectResponse,
    )
    def create_dmaic_voice_of_customer_study(
        project_id: RunId,
        request: SaveDmaicVoiceOfCustomerRequest,
        response: Response,
    ) -> StoredDmaicProjectResponse:
        stored, project = _load_dmaic_project(repository, project_id)
        if stored.storage_version != request.expected_storage_version:
            raise DocumentConflictError(
                f"Expected storage version {request.expected_storage_version}; found {stored.storage_version}."
            )
        revised, study = save_voice_of_customer(
            project,
            collection_plan=request.collection_plan,
            data_points=tuple(request.data_points),
            requirements=tuple(request.requirements),
            pain_points=tuple(request.pain_points),
            opportunities=tuple(request.opportunities),
            actions=tuple(request.actions),
            recommendations=tuple(request.recommendations),
            next_steps=tuple(request.next_steps),
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        _save_dmaic_voice_of_customer(repository, study)
        saved = _save_dmaic_project(
            repository, revised, expected_version=request.expected_storage_version
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _dmaic_project_response(saved)

    @app.get(
        "/v1/dmaic-projects/{project_id}/voice-of-customer-studies/{document_id}",
        response_model=StoredDmaicVoiceOfCustomerResponse,
    )
    def get_dmaic_voice_of_customer_study(
        project_id: RunId, document_id: RunId, response: Response
    ) -> StoredDmaicVoiceOfCustomerResponse:
        _stored_project, project = _load_dmaic_project(repository, project_id)
        stored = repository.load(DMAIC_VOICE_OF_CUSTOMER_STUDIES, document_id)
        study = _deserialize_dmaic_voice_of_customer(stored)
        if study.project_id != project.project_id:
            raise DocumentNotFoundError(
                f"Document {DMAIC_VOICE_OF_CUSTOMER_STUDIES}/{document_id} does not exist."
            )
        response.headers["ETag"] = f'"{stored.etag}"'
        return _dmaic_voice_of_customer_response(stored)

    @app.post("/v1/fmea-studies", status_code=201, response_model=StoredFmeaStudyResponse)
    def create_study(
        request: CreateFmeaStudyRequest, response: Response
    ) -> StoredFmeaStudyResponse:
        study = create_fmea_study(
            study_id=request.study_id,
            name=request.name,
            study_type=request.study_type,
            standard_version=request.standard_version,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        stored = _save_fmea_study(repository, study, expected_version=0)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _fmea_response(stored)

    @app.get("/v1/fmea-studies")
    def list_fmea_studies(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        after: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")] = None,
    ) -> dict[str, Any]:
        stored = repository.list_documents(FMEA_STUDIES, after=after, limit=limit + 1)
        has_more = len(stored) > limit
        page = stored[:limit]
        return {
            "items": [_fmea_response(item).model_dump() for item in page],
            "next_after": page[-1].key if has_more and page else None,
        }

    @app.get("/v1/fmea-studies/{study_id}", response_model=StoredFmeaStudyResponse)
    def get_fmea_study(study_id: RunId, response: Response) -> StoredFmeaStudyResponse:
        stored, _study = _load_fmea_study(repository, study_id)
        response.headers["ETag"] = f'"{stored.etag}"'
        return _fmea_response(stored)

    @app.get("/v1/fmea-studies/{study_id}/report")
    def get_fmea_study_report(study_id: RunId, response: Response) -> dict[str, Any]:
        _stored, study = _load_fmea_study(repository, study_id)
        report = build_study_report(
            study, evidence_checks=_check_fmea_analysis_evidence(repository, study)
        )
        response.headers["ETag"] = f'"{input_digest(report)}"'
        return report

    @app.post(
        "/v1/fmea-studies/{study_id}/action-priority-policy",
        response_model=StoredFmeaStudyResponse,
    )
    def attach_fmea_action_priority_policy(
        study_id: RunId,
        request: AttachActionPriorityPolicyRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        _policy_document, policy = _load_action_priority_policy(
            repository, request.policy_key
        )
        revised = attach_action_priority_policy(
            study,
            policy=policy,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/process-steps",
        response_model=StoredFmeaStudyResponse,
    )
    def add_fmea_process_step(
        study_id: RunId,
        request: AddProcessStepRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = add_process_step(
            study,
            step_id=request.step_id,
            sequence=request.sequence,
            name=request.name,
            operation=request.operation,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/process-characteristics",
        response_model=StoredFmeaStudyResponse,
    )
    def add_fmea_process_characteristic(
        study_id: RunId,
        request: AddProcessCharacteristicRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = add_process_characteristic(
            study,
            characteristic_id=request.characteristic_id,
            process_step_id=request.process_step_id,
            name=request.name,
            characteristic_type=request.characteristic_type,
            specification=request.specification,
            special_classification=request.special_classification,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/failure-analyses",
        response_model=StoredFmeaStudyResponse,
    )
    def add_fmea_failure(
        study_id: RunId,
        request: AddFailureAnalysisRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        policy = _load_attached_action_priority_policy(repository, study)
        revised = add_failure_analysis(
            study,
            item_id=request.item_id,
            structure_element=request.structure_element,
            function=request.function,
            requirement=request.requirement,
            failure_mode=request.failure_mode,
            effect=request.effect,
            cause=request.cause,
            prevention_control=request.prevention_control,
            detection_control=request.detection_control,
            ratings=RiskRatings(**request.ratings.model_dump()),
            actor=request.actor,
            occurred_at=request.occurred_at,
            policy=policy,
            process_step_id=request.process_step_id,
            characteristic_ids=tuple(request.characteristic_ids),
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/control-plan-items",
        response_model=StoredFmeaStudyResponse,
    )
    def add_fmea_control_plan_item(
        study_id: RunId,
        request: AddControlPlanItemRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = add_control_plan_item(
            study,
            control_id=request.control_id,
            phase=request.phase,
            characteristic_id=request.characteristic_id,
            failure_item_ids=tuple(request.failure_item_ids),
            measurement_method=request.measurement_method,
            sample_size=request.sample_size,
            frequency=request.frequency,
            control_method=request.control_method,
            reaction_plan=request.reaction_plan,
            reaction_owner=request.reaction_owner,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/control-plan-items/{control_id}/analysis-evidence",
        response_model=StoredFmeaStudyResponse,
    )
    def link_fmea_control_plan_analysis_evidence(
        study_id: RunId,
        control_id: RunId,
        request: LinkControlPlanAnalysisEvidenceRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = link_control_plan_analysis_evidence(
            study,
            control_id=control_id,
            reference=_load_analysis_evidence_reference(repository, request.run_id),
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/recommended-actions",
        response_model=StoredFmeaStudyResponse,
    )
    def add_fmea_action(
        study_id: RunId,
        request: AddRecommendedActionRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = add_recommended_action(
            study,
            action_id=request.action_id,
            item_id=request.item_id,
            description=request.description,
            owner=request.owner,
            due_date=request.due_date,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/recommended-actions/{action_id}/complete",
        response_model=StoredFmeaStudyResponse,
    )
    def complete_fmea_action(
        study_id: RunId,
        action_id: RunId,
        request: CompleteRecommendedActionRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        policy = _load_attached_action_priority_policy(repository, study)
        revised = complete_action(
            study,
            action_id=action_id,
            result=request.result,
            evidence_refs=tuple(request.evidence_refs),
            revised_ratings=RiskRatings(**request.revised_ratings.model_dump()),
            actor=request.actor,
            occurred_at=request.occurred_at,
            policy=policy,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/submit-review",
        response_model=StoredFmeaStudyResponse,
    )
    def submit_fmea_study(
        study_id: RunId,
        request: FmeaTransitionRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = submit_for_review(
            study,
            actor=request.actor,
            occurred_at=request.occurred_at,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    @app.post(
        "/v1/fmea-studies/{study_id}/approve",
        response_model=StoredFmeaStudyResponse,
    )
    def approve_fmea_study(
        study_id: RunId,
        request: ApproveFmeaStudyRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        if approval_authenticator is None:
            raise ApprovalConfigurationError(
                "Configure a local approval identity before approving studies."
            )
        principal = approval_authenticator.authenticate(
            request.user_id, request.password.get_secret_value()
        )
        authorization_context = approval_authenticator.authorization_context(
            signer_id=principal.user_id,
            prior_actors=tuple(event.actor for event in study.audit_events),
        )
        evidence_checks = _check_fmea_analysis_evidence(repository, study)
        failed_checks = [check for check in evidence_checks if check["status"] != "verified"]
        if failed_checks:
            raise FmeaInputError(
                "unverified_analysis_evidence_blocks_approval",
                "All linked SPC/MSA Runs must match before approval.",
                "analysis_evidence",
            )
        executed_at = datetime.now(UTC).isoformat()
        revised = approve_study(
            study,
            signature=ApprovalSignature(
                signer_id=principal.user_id,
                signer_name=principal.display_name,
                role=principal.role,
                meaning=request.meaning,
                authority=principal.authority,
                authentication_method=principal.authentication_method,
                signed_digest=study.digest,
                executed_at=executed_at,
            ),
            authorization_context=authorization_context,
        )
        saved = _save_fmea_study(
            repository,
            revised,
            expected_version=request.expected_storage_version,
        )
        response.headers["ETag"] = f'"{saved.etag}"'
        return _fmea_response(saved)

    return app


def create_local_app(
    storage_root: Path, approval_identity_file: Path | None = None
) -> FastAPI:
    identity_file = approval_identity_file or storage_root / "approval-identities.json"
    authenticator = (
        LocalApprovalAuthenticator.from_file(identity_file) if identity_file.exists() else None
    )
    return create_app(AtomicJsonDocumentRepository(storage_root), authenticator)
