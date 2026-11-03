"""State transitions for DMAIC project documents."""

from __future__ import annotations

from dataclasses import replace

from statpro.dmaic.models import (
    DmaicAnalysisEvidenceReference,
    DmaicCharter,
    DmaicDocumentReference,
    DmaicInputError,
    DmaicMeasurementPlan,
    DmaicProblemDefinition,
    DmaicProject,
    DmaicProjectStatus,
    DmaicSipocMap,
    DmaicStakeholder,
    DmaicStakeholderAssessment,
    DmaicVoiceOfCustomerStudy,
    _charter_digest,
    _measurement_plan_digest,
    _problem_definition_digest,
    _project_digest,
    _sipoc_digest,
    _stakeholder_assessment_digest,
    _voice_of_customer_digest,
)


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise DmaicInputError("required", f"{field} is required.", field)
    return normalized


def _optional(value: str | None) -> str | None:
    return None if value is None or not value.strip() else value.strip()


def _items(values: tuple[str, ...], field: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_required(value, field) for value in values))


def _positive_count(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or value <= 0:
        raise DmaicInputError("positive_count_required", f"{field} must be positive.", field)
    return value


def _score(value: int, field: str) -> int:
    if isinstance(value, bool) or value < 1 or value > 5:
        raise DmaicInputError("score_out_of_range", f"{field} must be between 1 and 5.", field)
    return value


def _choice(value: str, allowed: set[str], field: str) -> str:
    normalized = _required(value, field)
    if normalized not in allowed:
        raise DmaicInputError("invalid_choice", f"{field} is not supported.", field)
    return normalized


def create_project(*, project_id: str, title: str, owner_ref: str, sponsor_ref: str | None = None,
                   champion_ref: str | None = None, department: str | None = None,
                   start_date: str | None = None, target_end_date: str | None = None) -> DmaicProject:
    project = DmaicProject(project_id=_required(project_id, "project_id"), title=_required(title, "title"),
        owner_ref=_required(owner_ref, "owner_ref"), sponsor_ref=_optional(sponsor_ref), champion_ref=_optional(champion_ref),
        department=_optional(department), start_date=_optional(start_date), target_end_date=_optional(target_end_date),
        status=DmaicProjectStatus.DRAFT, revision=1, parent_digest=None, digest="", charter=None,
        voice_of_customer=None, sipoc=None, stakeholder_assessment=None, problem_definition=None,
        measurement_plan=None)
    return replace(project, digest=_project_digest(project))


def save_charter(project: DmaicProject, *, business_case: str, problem_statement: str,
                 scope_in: tuple[str, ...], scope_out: tuple[str, ...], success_metrics: tuple[str, ...],
                 team_refs: tuple[str, ...], budget: str | None, milestones: tuple[str, ...],
                 risk_refs: tuple[str, ...], assumptions_constraints: tuple[str, ...], actor: str,
                 occurred_at: str) -> tuple[DmaicProject, DmaicCharter]:
    previous = project.charter
    revision = 1 if previous is None else previous.revision + 1
    charter = DmaicCharter(document_id=f"{project.project_id}-charter-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        business_case=_required(business_case, "business_case"), problem_statement=_required(problem_statement, "problem_statement"),
        scope_in=_items(scope_in, "scope_in"), scope_out=_items(scope_out, "scope_out"),
        success_metrics=_items(success_metrics, "success_metrics"), team_refs=_items(team_refs, "team_refs"), budget=_optional(budget),
        milestones=_items(milestones, "milestones"), risk_refs=_items(risk_refs, "risk_refs"),
        assumptions_constraints=_items(assumptions_constraints, "assumptions_constraints"), actor=_required(actor, "actor"),
        occurred_at=_required(occurred_at, "occurred_at"))
    charter = replace(charter, digest=_charter_digest(charter))
    reference = DmaicDocumentReference("project_charter", charter.document_id, charter.revision, charter.digest)
    revised = replace(project, revision=project.revision + 1, parent_digest=project.digest, digest="", charter=reference)
    return replace(revised, digest=_project_digest(revised)), charter


def save_voice_of_customer(
    project: DmaicProject,
    *,
    collection_plan: str,
    data_points: tuple[str, ...],
    requirements: tuple[str, ...],
    pain_points: tuple[str, ...],
    opportunities: tuple[str, ...],
    actions: tuple[str, ...],
    recommendations: tuple[str, ...],
    next_steps: tuple[str, ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicVoiceOfCustomerStudy]:
    previous = project.voice_of_customer
    revision = 1 if previous is None else previous.revision + 1
    study = DmaicVoiceOfCustomerStudy(
        document_id=f"{project.project_id}-voc-r{revision}",
        project_id=project.project_id,
        revision=revision,
        parent_digest=None if previous is None else previous.digest,
        digest="",
        collection_plan=_required(collection_plan, "collection_plan"),
        data_points=_items(data_points, "data_points"),
        requirements=_items(requirements, "requirements"),
        pain_points=_items(pain_points, "pain_points"),
        opportunities=_items(opportunities, "opportunities"),
        actions=_items(actions, "actions"),
        recommendations=_items(recommendations, "recommendations"),
        next_steps=_items(next_steps, "next_steps"),
        actor=_required(actor, "actor"),
        occurred_at=_required(occurred_at, "occurred_at"),
    )
    study = replace(study, digest=_voice_of_customer_digest(study))
    reference = DmaicDocumentReference(
        "voice_of_customer", study.document_id, study.revision, study.digest
    )
    revised = replace(
        project,
        revision=project.revision + 1,
        parent_digest=project.digest,
        digest="",
        voice_of_customer=reference,
    )
    return replace(revised, digest=_project_digest(revised)), study


def save_sipoc(
    project: DmaicProject,
    *,
    process_start_boundary: str,
    process_end_boundary: str,
    suppliers: tuple[str, ...],
    inputs: tuple[str, ...],
    process_steps: tuple[str, ...],
    outputs: tuple[str, ...],
    customers: tuple[str, ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicSipocMap]:
    previous = project.sipoc
    revision = 1 if previous is None else previous.revision + 1
    sipoc = DmaicSipocMap(
        document_id=f"{project.project_id}-sipoc-r{revision}",
        project_id=project.project_id,
        revision=revision,
        parent_digest=None if previous is None else previous.digest,
        digest="",
        process_start_boundary=_required(process_start_boundary, "process_start_boundary"),
        process_end_boundary=_required(process_end_boundary, "process_end_boundary"),
        suppliers=_items(suppliers, "suppliers"),
        inputs=_items(inputs, "inputs"),
        process_steps=_items(process_steps, "process_steps"),
        outputs=_items(outputs, "outputs"),
        customers=_items(customers, "customers"),
        actor=_required(actor, "actor"),
        occurred_at=_required(occurred_at, "occurred_at"),
    )
    sipoc = replace(sipoc, digest=_sipoc_digest(sipoc))
    reference = DmaicDocumentReference("sipoc", sipoc.document_id, sipoc.revision, sipoc.digest)
    revised = replace(
        project,
        revision=project.revision + 1,
        parent_digest=project.digest,
        digest="",
        sipoc=reference,
    )
    return replace(revised, digest=_project_digest(revised)), sipoc


def save_stakeholder_assessment(
    project: DmaicProject,
    *,
    stakeholders: tuple[dict[str, object], ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicStakeholderAssessment]:
    """Save a new immutable stakeholder assessment revision for a project."""
    previous = project.stakeholder_assessment
    revision = 1 if previous is None else previous.revision + 1
    records = tuple(
        DmaicStakeholder(
            stakeholder_id=_required(str(item["stakeholder_id"]), "stakeholders.stakeholder_id"),
            name=_required(str(item["name"]), "stakeholders.name"),
            role=_required(str(item["role"]), "stakeholders.role"),
            department=_optional(item.get("department") if isinstance(item.get("department"), str) else None),
            influence=_score(item["influence"], "stakeholders.influence"),  # type: ignore[arg-type]
            interest=_score(item["interest"], "stakeholders.interest"),  # type: ignore[arg-type]
            attitude=_choice(str(item["attitude"]), {"supportive", "neutral", "resistant"}, "stakeholders.attitude"),
            communication=_choice(str(item["communication"]), {"low", "medium", "high"}, "stakeholders.communication"),
            concerns=_items(tuple(str(value) for value in item.get("concerns", ())), "stakeholders.concerns"),
            expectations=_items(tuple(str(value) for value in item.get("expectations", ())), "stakeholders.expectations"),
        )
        for item in stakeholders
    )
    if not records:
        raise DmaicInputError("stakeholders_required", "At least one stakeholder is required.", "stakeholders")
    if len({item.stakeholder_id for item in records}) != len(records):
        raise DmaicInputError("duplicate_stakeholder", "Stakeholder IDs must be unique.", "stakeholders")
    assessment = DmaicStakeholderAssessment(
        document_id=f"{project.project_id}-stakeholders-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        stakeholders=records, actor=_required(actor, "actor"), occurred_at=_required(occurred_at, "occurred_at"),
    )
    assessment = replace(assessment, digest=_stakeholder_assessment_digest(assessment))
    reference = DmaicDocumentReference(
        "stakeholder_assessment", assessment.document_id, assessment.revision, assessment.digest
    )
    revised = replace(
        project, revision=project.revision + 1, parent_digest=project.digest, digest="",
        stakeholder_assessment=reference,
    )
    return replace(revised, digest=_project_digest(revised)), assessment


def save_problem_definition(
    project: DmaicProject,
    *,
    problem_statement: str,
    impact: str,
    current_state: str,
    target_state: str,
    timeframe: str,
    location_scope: str,
    severity: str,
    urgency: str,
    objectives: tuple[str, ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicProblemDefinition]:
    """Save the project problem definition as an immutable Define-phase revision."""
    previous = project.problem_definition
    revision = 1 if previous is None else previous.revision + 1
    definition = DmaicProblemDefinition(
        document_id=f"{project.project_id}-problem-definition-r{revision}",
        project_id=project.project_id,
        revision=revision,
        parent_digest=None if previous is None else previous.digest,
        digest="",
        problem_statement=_required(problem_statement, "problem_statement"),
        impact=_required(impact, "impact"),
        current_state=_required(current_state, "current_state"),
        target_state=_required(target_state, "target_state"),
        timeframe=_required(timeframe, "timeframe"),
        location_scope=_required(location_scope, "location_scope"),
        severity=_choice(severity, {"low", "medium", "high"}, "severity"),
        urgency=_choice(urgency, {"low", "medium", "high"}, "urgency"),
        objectives=_items(objectives, "objectives"),
        actor=_required(actor, "actor"),
        occurred_at=_required(occurred_at, "occurred_at"),
    )
    definition = replace(definition, digest=_problem_definition_digest(definition))
    reference = DmaicDocumentReference(
        "problem_definition", definition.document_id, definition.revision, definition.digest
    )
    revised = replace(
        project,
        revision=project.revision + 1,
        parent_digest=project.digest,
        digest="",
        problem_definition=reference,
    )
    return replace(revised, digest=_project_digest(revised)), definition


def save_measurement_plan(
    project: DmaicProject,
    *,
    primary_metric: str,
    data_source: str,
    collection_method: str,
    collection_frequency: str,
    sampling_method: str,
    sample_size: int | None,
    analysis_evidence: tuple[dict[str, str], ...],
    actor: str,
    occurred_at: str,
    baseline_value: float | None = None,
    target_value: float | None = None,
    population_size: int | None = None,
    sampling_rationale: str | None = None,
    measurement_instrument: str | None = None,
    measurement_unit: str | None = None,
    measurement_precision: str | None = None,
    calibration_required: bool = False,
    msa_required: bool = False,
) -> tuple[DmaicProject, DmaicMeasurementPlan]:
    previous = project.measurement_plan
    revision = 1 if previous is None else previous.revision + 1
    evidence = tuple(
        DmaicAnalysisEvidenceReference(
            run_id=_required(reference["run_id"], "analysis_evidence.run_id"),
            analysis_type=_required(reference["analysis_type"], "analysis_evidence.analysis_type"),
            run_etag=_required(reference["run_etag"], "analysis_evidence.run_etag"),
            input_digest=_required(reference["input_digest"], "analysis_evidence.input_digest"),
        )
        for reference in analysis_evidence
    )
    if len({reference.run_id for reference in evidence}) != len(evidence):
        raise DmaicInputError("duplicate_analysis_evidence", "Analysis evidence Run IDs must be unique.", "analysis_evidence")
    source_documents = tuple(
        reference
        for reference in (
            project.charter,
            project.voice_of_customer,
            project.sipoc,
            project.stakeholder_assessment,
            project.problem_definition,
        )
        if reference is not None
    )
    plan = DmaicMeasurementPlan(
        document_id=f"{project.project_id}-measurement-plan-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        primary_metric=_required(primary_metric, "primary_metric"), baseline_value=baseline_value,
        target_value=target_value, data_source=_required(data_source, "data_source"),
        collection_method=_required(collection_method, "collection_method"),
        collection_frequency=_required(collection_frequency, "collection_frequency"),
        sampling_method=_required(sampling_method, "sampling_method"),
        population_size=_positive_count(population_size, "population_size"),
        sample_size=_positive_count(sample_size, "sample_size"),
        sampling_rationale=_optional(sampling_rationale), measurement_instrument=_optional(measurement_instrument),
        measurement_unit=_optional(measurement_unit), measurement_precision=_optional(measurement_precision),
        calibration_required=calibration_required, msa_required=msa_required,
        source_documents=source_documents, analysis_evidence=evidence,
        actor=_required(actor, "actor"), occurred_at=_required(occurred_at, "occurred_at"),
    )
    plan = replace(plan, digest=_measurement_plan_digest(plan))
    reference = DmaicDocumentReference("measurement_plan", plan.document_id, plan.revision, plan.digest)
    revised = replace(
        project, revision=project.revision + 1, parent_digest=project.digest, digest="",
        measurement_plan=reference,
    )
    return replace(revised, digest=_project_digest(revised)), plan
