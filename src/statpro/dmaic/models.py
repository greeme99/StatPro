"""Immutable entities owned by the DMAIC project bounded context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest


class DmaicInputError(DomainInputError):
    """An expected, user-correctable DMAIC project failure."""


class DmaicProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class DmaicDocumentReference:
    document_type: str
    document_id: str
    revision: int
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DmaicAnalysisEvidenceReference:
    """The immutable identity of an analysis Run used by a DMAIC document."""

    run_id: str
    analysis_type: str
    run_etag: str
    input_digest: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DmaicFmeaControlPlanReference:
    """Immutable identity of the FMEA control-plan snapshot used for handoff."""

    study_id: str
    study_etag: str
    study_digest: str
    control_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "control_ids": list(self.control_ids)}


@dataclass(frozen=True, slots=True)
class DmaicReactionPlanItem:
    trigger: str
    action: str
    owner_ref: str
    escalation_ref: str | None
    response_time: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DmaicProject:
    project_id: str
    title: str
    owner_ref: str
    sponsor_ref: str | None
    champion_ref: str | None
    department: str | None
    start_date: str | None
    target_end_date: str | None
    status: DmaicProjectStatus
    revision: int
    parent_digest: str | None
    digest: str
    charter: DmaicDocumentReference | None = None
    voice_of_customer: DmaicDocumentReference | None = None
    sipoc: DmaicDocumentReference | None = None
    stakeholder_assessment: DmaicDocumentReference | None = None
    problem_definition: DmaicDocumentReference | None = None
    measurement_plan: DmaicDocumentReference | None = None
    root_cause_analysis: DmaicDocumentReference | None = None
    solution_selection: DmaicDocumentReference | None = None
    pilot_plan: DmaicDocumentReference | None = None
    control_handoff: DmaicDocumentReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "owner_ref": self.owner_ref,
            "sponsor_ref": self.sponsor_ref,
            "champion_ref": self.champion_ref,
            "department": self.department,
            "start_date": self.start_date,
            "target_end_date": self.target_end_date,
            "status": self.status.value,
            "revision": self.revision,
            "parent_digest": self.parent_digest,
            "digest": self.digest,
            "charter": None if self.charter is None else self.charter.to_dict(),
            "voice_of_customer": (
                None if self.voice_of_customer is None else self.voice_of_customer.to_dict()
            ),
            "sipoc": None if self.sipoc is None else self.sipoc.to_dict(),
            "stakeholder_assessment": (
                None
                if self.stakeholder_assessment is None
                else self.stakeholder_assessment.to_dict()
            ),
            "problem_definition": (
                None
                if self.problem_definition is None
                else self.problem_definition.to_dict()
            ),
            "measurement_plan": (
                None if self.measurement_plan is None else self.measurement_plan.to_dict()
            ),
            "root_cause_analysis": (
                None if self.root_cause_analysis is None else self.root_cause_analysis.to_dict()
            ),
            "solution_selection": (
                None if self.solution_selection is None else self.solution_selection.to_dict()
            ),
            "pilot_plan": None if self.pilot_plan is None else self.pilot_plan.to_dict(),
            "control_handoff": (
                None if self.control_handoff is None else self.control_handoff.to_dict()
            ),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicProject:
        reference = payload.get("charter")
        voice_of_customer = payload.get("voice_of_customer")
        sipoc = payload.get("sipoc")
        stakeholder_assessment = payload.get("stakeholder_assessment")
        problem_definition = payload.get("problem_definition")
        measurement_plan = payload.get("measurement_plan")
        root_cause_analysis = payload.get("root_cause_analysis")
        solution_selection = payload.get("solution_selection")
        pilot_plan = payload.get("pilot_plan")
        control_handoff = payload.get("control_handoff")
        project = cls(
            project_id=payload["project_id"], title=payload["title"], owner_ref=payload["owner_ref"],
            sponsor_ref=payload.get("sponsor_ref"), champion_ref=payload.get("champion_ref"),
            department=payload.get("department"), start_date=payload.get("start_date"),
            target_end_date=payload.get("target_end_date"), status=DmaicProjectStatus(payload["status"]),
            revision=payload["revision"], parent_digest=payload.get("parent_digest"), digest=payload["digest"],
            charter=None if reference is None else DmaicDocumentReference(**reference),
            voice_of_customer=(
                None
                if voice_of_customer is None
                else DmaicDocumentReference(**voice_of_customer)
            ),
            sipoc=None if sipoc is None else DmaicDocumentReference(**sipoc),
            stakeholder_assessment=(
                None
                if stakeholder_assessment is None
                else DmaicDocumentReference(**stakeholder_assessment)
            ),
            problem_definition=(
                None
                if problem_definition is None
                else DmaicDocumentReference(**problem_definition)
            ),
            measurement_plan=(
                None
                if measurement_plan is None
                else DmaicDocumentReference(**measurement_plan)
            ),
            root_cause_analysis=(
                None
                if root_cause_analysis is None
                else DmaicDocumentReference(**root_cause_analysis)
            ),
            solution_selection=(
                None
                if solution_selection is None
                else DmaicDocumentReference(**solution_selection)
            ),
            pilot_plan=None if pilot_plan is None else DmaicDocumentReference(**pilot_plan),
            control_handoff=(
                None
                if control_handoff is None
                else DmaicDocumentReference(**control_handoff)
            ),
        )
        if project.digest != _project_digest(project):
            raise DmaicInputError("project_digest_mismatch", "Stored DMAIC project digest does not match.", "digest")
        return project


@dataclass(frozen=True, slots=True)
class DmaicCharter:
    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    business_case: str
    problem_statement: str
    scope_in: tuple[str, ...]
    scope_out: tuple[str, ...]
    success_metrics: tuple[str, ...]
    team_refs: tuple[str, ...]
    budget: str | None
    milestones: tuple[str, ...]
    risk_refs: tuple[str, ...]
    assumptions_constraints: tuple[str, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "scope_in": list(self.scope_in), "scope_out": list(self.scope_out),
                "success_metrics": list(self.success_metrics), "team_refs": list(self.team_refs),
                "milestones": list(self.milestones), "risk_refs": list(self.risk_refs),
                "assumptions_constraints": list(self.assumptions_constraints)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicCharter:
        charter = cls(
            document_id=payload["document_id"], project_id=payload["project_id"], revision=payload["revision"],
            parent_digest=payload.get("parent_digest"), digest=payload["digest"],
            business_case=payload["business_case"], problem_statement=payload["problem_statement"],
            scope_in=tuple(payload["scope_in"]), scope_out=tuple(payload["scope_out"]),
            success_metrics=tuple(payload["success_metrics"]), team_refs=tuple(payload["team_refs"]),
            budget=payload.get("budget"), milestones=tuple(payload["milestones"]), risk_refs=tuple(payload["risk_refs"]),
            assumptions_constraints=tuple(payload["assumptions_constraints"]), actor=payload["actor"],
            occurred_at=payload["occurred_at"],
        )
        if charter.digest != _charter_digest(charter):
            raise DmaicInputError("charter_digest_mismatch", "Stored charter digest does not match.", "digest")
        return charter


@dataclass(frozen=True, slots=True)
class DmaicVoiceOfCustomerStudy:
    """An immutable Define-phase record of customer needs and planned actions."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    collection_plan: str
    data_points: tuple[str, ...]
    requirements: tuple[str, ...]
    pain_points: tuple[str, ...]
    opportunities: tuple[str, ...]
    actions: tuple[str, ...]
    recommendations: tuple[str, ...]
    next_steps: tuple[str, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "data_points": list(self.data_points),
            "requirements": list(self.requirements),
            "pain_points": list(self.pain_points),
            "opportunities": list(self.opportunities),
            "actions": list(self.actions),
            "recommendations": list(self.recommendations),
            "next_steps": list(self.next_steps),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicVoiceOfCustomerStudy:
        study = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], collection_plan=payload["collection_plan"],
            data_points=tuple(payload["data_points"]), requirements=tuple(payload["requirements"]),
            pain_points=tuple(payload["pain_points"]), opportunities=tuple(payload["opportunities"]),
            actions=tuple(payload["actions"]), recommendations=tuple(payload["recommendations"]),
            next_steps=tuple(payload["next_steps"]), actor=payload["actor"],
            occurred_at=payload["occurred_at"],
        )
        if study.digest != _voice_of_customer_digest(study):
            raise DmaicInputError(
                "voice_of_customer_digest_mismatch",
                "Stored Voice of Customer study digest does not match.",
                "digest",
            )
        return study


@dataclass(frozen=True, slots=True)
class DmaicSipocMap:
    """An immutable Define-phase map of process boundaries and SIPOC elements."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    process_start_boundary: str
    process_end_boundary: str
    suppliers: tuple[str, ...]
    inputs: tuple[str, ...]
    process_steps: tuple[str, ...]
    outputs: tuple[str, ...]
    customers: tuple[str, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "suppliers": list(self.suppliers),
            "inputs": list(self.inputs),
            "process_steps": list(self.process_steps),
            "outputs": list(self.outputs),
            "customers": list(self.customers),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicSipocMap:
        sipoc = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], process_start_boundary=payload["process_start_boundary"],
            process_end_boundary=payload["process_end_boundary"], suppliers=tuple(payload["suppliers"]),
            inputs=tuple(payload["inputs"]), process_steps=tuple(payload["process_steps"]),
            outputs=tuple(payload["outputs"]), customers=tuple(payload["customers"]),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if sipoc.digest != _sipoc_digest(sipoc):
            raise DmaicInputError(
                "sipoc_digest_mismatch", "Stored SIPOC map digest does not match.", "digest"
            )
        return sipoc


@dataclass(frozen=True, slots=True)
class DmaicStakeholder:
    """A project stakeholder with explicit influence, interest, and engagement intent."""

    stakeholder_id: str
    name: str
    role: str
    department: str | None
    influence: int
    interest: int
    attitude: str
    communication: str
    concerns: tuple[str, ...]
    expectations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "concerns": list(self.concerns),
            "expectations": list(self.expectations),
        }


@dataclass(frozen=True, slots=True)
class DmaicStakeholderAssessment:
    """An immutable Define-phase stakeholder assessment for a DMAIC project."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    stakeholders: tuple[DmaicStakeholder, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "stakeholders": [item.to_dict() for item in self.stakeholders]}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicStakeholderAssessment:
        assessment = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"],
            stakeholders=tuple(
                DmaicStakeholder(
                    stakeholder_id=item["stakeholder_id"], name=item["name"], role=item["role"],
                    department=item.get("department"), influence=item["influence"],
                    interest=item["interest"], attitude=item["attitude"], communication=item["communication"],
                    concerns=tuple(item.get("concerns", [])), expectations=tuple(item.get("expectations", [])),
                )
                for item in payload["stakeholders"]
            ),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if assessment.digest != _stakeholder_assessment_digest(assessment):
            raise DmaicInputError(
                "stakeholder_assessment_digest_mismatch",
                "Stored stakeholder assessment digest does not match.",
                "digest",
            )
        return assessment


@dataclass(frozen=True, slots=True)
class DmaicProblemDefinition:
    """An immutable Define-phase statement of the problem, gap, and decision urgency."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    problem_statement: str
    impact: str
    current_state: str
    target_state: str
    timeframe: str
    location_scope: str
    severity: str
    urgency: str
    objectives: tuple[str, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "objectives": list(self.objectives)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicProblemDefinition:
        definition = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], problem_statement=payload["problem_statement"],
            impact=payload["impact"], current_state=payload["current_state"],
            target_state=payload["target_state"], timeframe=payload["timeframe"],
            location_scope=payload["location_scope"], severity=payload["severity"],
            urgency=payload["urgency"], objectives=tuple(payload["objectives"]),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if definition.digest != _problem_definition_digest(definition):
            raise DmaicInputError(
                "problem_definition_digest_mismatch",
                "Stored problem definition digest does not match.",
                "digest",
            )
        return definition


@dataclass(frozen=True, slots=True)
class DmaicMeasurementPlan:
    """Immutable Measure-phase plan with Define-document and analysis evidence links."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    primary_metric: str
    baseline_value: float | None
    target_value: float | None
    data_source: str
    collection_method: str
    collection_frequency: str
    sampling_method: str
    population_size: int | None
    sample_size: int | None
    sampling_rationale: str | None
    measurement_instrument: str | None
    measurement_unit: str | None
    measurement_precision: str | None
    calibration_required: bool
    msa_required: bool
    source_documents: tuple[DmaicDocumentReference, ...]
    analysis_evidence: tuple[DmaicAnalysisEvidenceReference, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "source_documents": [reference.to_dict() for reference in self.source_documents],
            "analysis_evidence": [reference.to_dict() for reference in self.analysis_evidence],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicMeasurementPlan:
        plan = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], primary_metric=payload["primary_metric"],
            baseline_value=payload.get("baseline_value"), target_value=payload.get("target_value"),
            data_source=payload["data_source"], collection_method=payload["collection_method"],
            collection_frequency=payload["collection_frequency"], sampling_method=payload["sampling_method"],
            population_size=payload.get("population_size"), sample_size=payload.get("sample_size"),
            sampling_rationale=payload.get("sampling_rationale"),
            measurement_instrument=payload.get("measurement_instrument"),
            measurement_unit=payload.get("measurement_unit"),
            measurement_precision=payload.get("measurement_precision"),
            calibration_required=payload["calibration_required"], msa_required=payload["msa_required"],
            source_documents=tuple(
                DmaicDocumentReference(**reference)
                for reference in payload.get("source_documents", [])
            ),
            analysis_evidence=tuple(
                DmaicAnalysisEvidenceReference(**reference)
                for reference in payload.get("analysis_evidence", [])
            ),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if plan.digest != _measurement_plan_digest(plan):
            raise DmaicInputError(
                "measurement_plan_digest_mismatch",
                "Stored measurement plan digest does not match.",
                "digest",
            )
        return plan


@dataclass(frozen=True, slots=True)
class DmaicRootCauseAnalysis:
    """Immutable Analyze-phase decision record with upstream and Run evidence."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    problem_statement: str
    method: str
    candidate_causes: tuple[str, ...]
    verified_causes: tuple[str, ...]
    next_actions: tuple[str, ...]
    source_documents: tuple[DmaicDocumentReference, ...]
    analysis_evidence: tuple[DmaicAnalysisEvidenceReference, ...]
    actor: str
    occurred_at: str
    why_chain: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "candidate_causes": list(self.candidate_causes),
            "verified_causes": list(self.verified_causes),
            "next_actions": list(self.next_actions),
            **({"why_chain": list(self.why_chain)} if self.why_chain else {}),
            "source_documents": [item.to_dict() for item in self.source_documents],
            "analysis_evidence": [item.to_dict() for item in self.analysis_evidence],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicRootCauseAnalysis:
        analysis = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], problem_statement=payload["problem_statement"], method=payload["method"],
            candidate_causes=tuple(payload["candidate_causes"]), verified_causes=tuple(payload["verified_causes"]),
            next_actions=tuple(payload["next_actions"]),
            source_documents=tuple(DmaicDocumentReference(**item) for item in payload.get("source_documents", [])),
            analysis_evidence=tuple(DmaicAnalysisEvidenceReference(**item) for item in payload.get("analysis_evidence", [])),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
            why_chain=tuple(payload.get("why_chain", [])),
        )
        if analysis.digest != _root_cause_analysis_digest(analysis):
            raise DmaicInputError("root_cause_analysis_digest_mismatch", "Stored root cause analysis digest does not match.", "digest")
        return analysis


@dataclass(frozen=True, slots=True)
class DmaicSolutionSelection:
    """Immutable Improve-phase decision with root-cause and Run evidence."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    problem_statement: str
    candidate_solutions: tuple[str, ...]
    selected_solution: str
    decision_rationale: str
    validation_plan: str
    source_documents: tuple[DmaicDocumentReference, ...]
    analysis_evidence: tuple[DmaicAnalysisEvidenceReference, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "candidate_solutions": list(self.candidate_solutions),
            "source_documents": [item.to_dict() for item in self.source_documents],
            "analysis_evidence": [item.to_dict() for item in self.analysis_evidence],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicSolutionSelection:
        selection = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], problem_statement=payload["problem_statement"],
            candidate_solutions=tuple(payload["candidate_solutions"]),
            selected_solution=payload["selected_solution"],
            decision_rationale=payload["decision_rationale"], validation_plan=payload["validation_plan"],
            source_documents=tuple(DmaicDocumentReference(**item) for item in payload.get("source_documents", [])),
            analysis_evidence=tuple(DmaicAnalysisEvidenceReference(**item) for item in payload.get("analysis_evidence", [])),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if selection.digest != _solution_selection_digest(selection):
            raise DmaicInputError("solution_selection_digest_mismatch", "Stored solution selection digest does not match.", "digest")
        return selection


@dataclass(frozen=True, slots=True)
class DmaicPilotPlan:
    """Immutable Improve-phase pilot plan with selection and Run evidence."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    pilot_type: str
    scope: str
    study_design: str
    sample_plan: str
    duration: str
    success_metrics: tuple[str, ...]
    stop_criteria: tuple[str, ...]
    risk_responses: tuple[str, ...]
    source_documents: tuple[DmaicDocumentReference, ...]
    analysis_evidence: tuple[DmaicAnalysisEvidenceReference, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "success_metrics": list(self.success_metrics),
            "stop_criteria": list(self.stop_criteria),
            "risk_responses": list(self.risk_responses),
            "source_documents": [item.to_dict() for item in self.source_documents],
            "analysis_evidence": [item.to_dict() for item in self.analysis_evidence],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicPilotPlan:
        plan = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], pilot_type=payload["pilot_type"], scope=payload["scope"],
            study_design=payload["study_design"], sample_plan=payload["sample_plan"],
            duration=payload["duration"], success_metrics=tuple(payload["success_metrics"]),
            stop_criteria=tuple(payload["stop_criteria"]), risk_responses=tuple(payload["risk_responses"]),
            source_documents=tuple(DmaicDocumentReference(**item) for item in payload.get("source_documents", [])),
            analysis_evidence=tuple(DmaicAnalysisEvidenceReference(**item) for item in payload.get("analysis_evidence", [])),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if plan.digest != _pilot_plan_digest(plan):
            raise DmaicInputError("pilot_plan_digest_mismatch", "Stored pilot plan digest does not match.", "digest")
        return plan


@dataclass(frozen=True, slots=True)
class DmaicControlHandoff:
    """Immutable Control-phase operating contract and evidence handoff."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    monitoring_plan: str
    review_frequency: str
    effectiveness_criteria: tuple[str, ...]
    reaction_plans: tuple[DmaicReactionPlanItem, ...]
    source_documents: tuple[DmaicDocumentReference, ...]
    fmea_control_plan: DmaicFmeaControlPlanReference
    analysis_evidence: tuple[DmaicAnalysisEvidenceReference, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "effectiveness_criteria": list(self.effectiveness_criteria),
            "reaction_plans": [item.to_dict() for item in self.reaction_plans],
            "source_documents": [item.to_dict() for item in self.source_documents],
            "fmea_control_plan": self.fmea_control_plan.to_dict(),
            "analysis_evidence": [item.to_dict() for item in self.analysis_evidence],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicControlHandoff:
        fmea = payload["fmea_control_plan"]
        handoff = cls(
            document_id=payload["document_id"], project_id=payload["project_id"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"], monitoring_plan=payload["monitoring_plan"],
            review_frequency=payload["review_frequency"],
            effectiveness_criteria=tuple(payload["effectiveness_criteria"]),
            reaction_plans=tuple(DmaicReactionPlanItem(**item) for item in payload["reaction_plans"]),
            source_documents=tuple(DmaicDocumentReference(**item) for item in payload.get("source_documents", [])),
            fmea_control_plan=DmaicFmeaControlPlanReference(
                study_id=fmea["study_id"], study_etag=fmea["study_etag"],
                study_digest=fmea["study_digest"], control_ids=tuple(fmea["control_ids"]),
            ),
            analysis_evidence=tuple(DmaicAnalysisEvidenceReference(**item) for item in payload.get("analysis_evidence", [])),
            actor=payload["actor"], occurred_at=payload["occurred_at"],
        )
        if handoff.digest != _control_handoff_digest(handoff):
            raise DmaicInputError("control_handoff_digest_mismatch", "Stored control handoff digest does not match.", "digest")
        return handoff


def _project_digest(project: DmaicProject) -> str:
    payload = project.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _charter_digest(charter: DmaicCharter) -> str:
    payload = charter.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _voice_of_customer_digest(study: DmaicVoiceOfCustomerStudy) -> str:
    payload = study.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _sipoc_digest(sipoc: DmaicSipocMap) -> str:
    payload = sipoc.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _stakeholder_assessment_digest(assessment: DmaicStakeholderAssessment) -> str:
    payload = assessment.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _problem_definition_digest(definition: DmaicProblemDefinition) -> str:
    payload = definition.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _measurement_plan_digest(plan: DmaicMeasurementPlan) -> str:
    payload = plan.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _root_cause_analysis_digest(analysis: DmaicRootCauseAnalysis) -> str:
    payload = analysis.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _solution_selection_digest(selection: DmaicSolutionSelection) -> str:
    payload = selection.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _pilot_plan_digest(plan: DmaicPilotPlan) -> str:
    payload = plan.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _control_handoff_digest(handoff: DmaicControlHandoff) -> str:
    payload = handoff.to_dict()
    payload.pop("digest")
    return input_digest(payload)
