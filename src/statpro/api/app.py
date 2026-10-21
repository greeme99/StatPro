"""FastAPI adapter over the StatPro statistical core and document seam."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    ResponseObjective,
    analyze_full_factorial_2level,
    fractional_factorial_2level,
    full_factorial_2level,
    optimize_full_factorial_desirability,
    plackett_burman_design,
)
from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed
from statpro.analyses.spc import individuals_moving_range, xbar_r
from statpro.application.documents import (
    AtomicJsonDocumentRepository,
    DocumentConflictError,
    DocumentNotFoundError,
    DocumentRepository,
    DocumentStoreError,
    InvalidDocumentKeyError,
    StoredDocument,
)
from statpro.domain.errors import AnalysisInputError, DomainInputError
from statpro.domain.data import (
    DataType,
    DatasetSnapshot,
    WorksheetSnapshot,
    create_worksheet,
    import_csv_bytes,
    replace_worksheet_cell,
)
from statpro.domain.models import ResultBundle
from statpro.domain.schema import result_bundle_schema
from statpro.fmea import (
    FmeaStudySnapshot,
    RiskRatings,
    StudyType,
    add_failure_analysis,
    add_recommended_action,
    approve_study,
    complete_action,
    create_fmea_study,
    submit_for_review,
)
from statpro.version import ENGINE_VERSION

ANALYSIS_RUNS = "analysis-runs"
DATASETS = "datasets"
WORKSHEETS = "worksheets"
FMEA_STUDIES = "fmea-studies"
RunId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImrRunRequest(ApiModel):
    run_id: RunId
    values: list[float]
    target: float | None = None
    rules: Literal["basic", "western_electric", "nelson"] = "western_electric"


class XbarRRunRequest(ApiModel):
    run_id: RunId
    subgroups: list[list[float]]
    rules: Literal["basic", "nelson"] = "basic"


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
    randomize: bool = True
    seed: int = 0


class GeneratorRequest(ApiModel):
    factor: str
    terms: list[str] = Field(min_length=2)


class FractionalFactorialRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest]
    generators: list[GeneratorRequest] = Field(min_length=1, max_length=8)
    replicates: int = 1
    randomize: bool = True
    seed: int = 0


class PlackettBurmanRunRequest(ApiModel):
    run_id: RunId
    factors: list[FactorRequest] = Field(min_length=2, max_length=47)
    runs: Literal[12, 20, 24, 28, 32, 36, 40, 44, 48] | None = None
    replicates: int = 1
    center_points: int = 0
    randomize: bool = True
    seed: int = 0


class FullFactorialAnalysisRunRequest(FullFactorialRunRequest):
    responses: list[float]
    response_name: str = "Response"
    interaction_order: int = Field(default=2, ge=1)
    prediction_points: list[dict[str, float]] = Field(default_factory=list, max_length=100)
    optimization_goal: Literal["maximize", "minimize"] | None = None


class ResponseObjectiveRequest(ApiModel):
    name: str
    responses: list[float]
    goal: Literal["maximize", "minimize", "target"]
    target: float
    lower: float | None = None
    upper: float | None = None
    weight: float = 1.0
    importance: float = 1.0


class FullFactorialOptimizerRunRequest(FullFactorialRunRequest):
    objectives: list[ResponseObjectiveRequest] = Field(min_length=1, max_length=10)
    interaction_order: int = Field(default=2, ge=1)


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
    actor: str
    occurred_at: str


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


class StoredFmeaStudyResponse(ApiModel):
    study_id: str
    storage_version: int
    etag: str
    study: dict[str, Any]


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
    return StoredFmeaStudyResponse(
        study_id=stored.key,
        storage_version=stored.storage_version,
        etag=stored.etag,
        study=stored.document["study"],
    )


def _load_fmea_study(repository: DocumentRepository, study_id: str) -> tuple[StoredDocument, FmeaStudySnapshot]:
    stored = repository.load(FMEA_STUDIES, study_id)
    try:
        study = FmeaStudySnapshot.from_dict(stored.document["study"])
    except (KeyError, TypeError, ValueError) as error:
        raise DocumentStoreError(
            f"Stored FMEA study {study_id} does not match its owned format."
        ) from error
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


def create_app(repository: DocumentRepository) -> FastAPI:
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
                replicates=request.replicates,
                randomize=request.randomize,
                seed=request.seed,
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

    @app.post(
        "/v1/fmea-studies/{study_id}/failure-analyses",
        response_model=StoredFmeaStudyResponse,
    )
    def add_fmea_failure(
        study_id: RunId,
        request: AddFailureAnalysisRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        stored, study = _load_fmea_study(repository, study_id)
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
        revised = complete_action(
            study,
            action_id=action_id,
            result=request.result,
            evidence_refs=tuple(request.evidence_refs),
            revised_ratings=RiskRatings(**request.revised_ratings.model_dump()),
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
        request: FmeaTransitionRequest,
        response: Response,
    ) -> StoredFmeaStudyResponse:
        _stored, study = _load_fmea_study(repository, study_id)
        revised = approve_study(
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

    return app


def create_local_app(storage_root: Path) -> FastAPI:
    return create_app(AtomicJsonDocumentRepository(storage_root))
