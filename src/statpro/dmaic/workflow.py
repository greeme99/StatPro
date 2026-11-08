"""State transitions for DMAIC project documents."""

from __future__ import annotations

from dataclasses import replace

from statpro.dmaic.models import (
    DmaicAnalysisEvidenceReference,
    DmaicCharter,
    DmaicControlHandoff,
    DmaicDocumentReference,
    DmaicFmeaControlPlanReference,
    DmaicInputError,
    DmaicMeasurementPlan,
    DmaicPilotPlan,
    DmaicProblemDefinition,
    DmaicProject,
    DmaicProjectStatus,
    DmaicReactionPlanItem,
    DmaicRootCauseAnalysis,
    DmaicSipocMap,
    DmaicSolutionSelection,
    DmaicStakeholder,
    DmaicStakeholderAssessment,
    DmaicVoiceOfCustomerStudy,
    _charter_digest,
    _control_handoff_digest,
    _measurement_plan_digest,
    _pilot_plan_digest,
    _problem_definition_digest,
    _project_digest,
    _root_cause_analysis_digest,
    _sipoc_digest,
    _solution_selection_digest,
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
        measurement_plan=None, root_cause_analysis=None)
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


def save_root_cause_analysis(
    project: DmaicProject,
    *,
    problem_statement: str,
    method: str,
    candidate_causes: tuple[str, ...],
    verified_causes: tuple[str, ...],
    next_actions: tuple[str, ...],
    analysis_evidence: tuple[dict[str, str], ...],
    actor: str,
    occurred_at: str,
    why_chain: tuple[str, ...] = (),
) -> tuple[DmaicProject, DmaicRootCauseAnalysis]:
    """Save an Analyze decision, retaining selected source and Run evidence."""
    previous = project.root_cause_analysis
    revision = 1 if previous is None else previous.revision + 1
    evidence = tuple(
        DmaicAnalysisEvidenceReference(
            run_id=_required(item["run_id"], "analysis_evidence.run_id"),
            analysis_type=_required(item["analysis_type"], "analysis_evidence.analysis_type"),
            run_etag=_required(item["run_etag"], "analysis_evidence.run_etag"),
            input_digest=_required(item["input_digest"], "analysis_evidence.input_digest"),
        )
        for item in analysis_evidence
    )
    if len({item.run_id for item in evidence}) != len(evidence):
        raise DmaicInputError("duplicate_analysis_evidence", "Analysis evidence Run IDs must be unique.", "analysis_evidence")
    sources = tuple(item for item in (
        project.problem_definition, project.measurement_plan, project.sipoc, project.charter
    ) if item is not None)
    normalized_method = _choice(method, {"fishbone_pareto", "five_whys", "data_analysis"}, "method")
    normalized_why_chain = _items(why_chain, "why_chain") if why_chain else ()
    if normalized_method == "five_whys" and len(normalized_why_chain) != 5:
        raise DmaicInputError("five_whys_requires_five_steps", "5 Why requires exactly five question-and-answer steps.", "why_chain")
    if normalized_method != "five_whys" and normalized_why_chain:
        raise DmaicInputError("five_whys_method_required", "why_chain requires the five_whys method.", "method")
    analysis = DmaicRootCauseAnalysis(
        document_id=f"{project.project_id}-root-cause-analysis-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        problem_statement=_required(problem_statement, "problem_statement"),
        method=normalized_method,
        candidate_causes=_items(candidate_causes, "candidate_causes"),
        verified_causes=_items(verified_causes, "verified_causes"), next_actions=_items(next_actions, "next_actions"),
        source_documents=sources, analysis_evidence=evidence,
        actor=_required(actor, "actor"), occurred_at=_required(occurred_at, "occurred_at"),
        why_chain=normalized_why_chain,
    )
    analysis = replace(analysis, digest=_root_cause_analysis_digest(analysis))
    reference = DmaicDocumentReference("root_cause_analysis", analysis.document_id, analysis.revision, analysis.digest)
    revised = replace(project, revision=project.revision + 1, parent_digest=project.digest, digest="", root_cause_analysis=reference)
    return replace(revised, digest=_project_digest(revised)), analysis


def save_solution_selection(
    project: DmaicProject,
    *,
    problem_statement: str,
    candidate_solutions: tuple[str, ...],
    selected_solution: str,
    decision_rationale: str,
    validation_plan: str,
    analysis_evidence: tuple[dict[str, str], ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicSolutionSelection]:
    """Save an Improve decision and retain the root-cause and Run evidence used."""
    previous = project.solution_selection
    revision = 1 if previous is None else previous.revision + 1
    candidates = _items(candidate_solutions, "candidate_solutions")
    selected = _required(selected_solution, "selected_solution")
    if selected not in candidates:
        raise DmaicInputError(
            "selected_solution_not_candidate",
            "selected_solution must be one of candidate_solutions.",
            "selected_solution",
        )
    evidence = tuple(
        DmaicAnalysisEvidenceReference(
            run_id=_required(item["run_id"], "analysis_evidence.run_id"),
            analysis_type=_required(item["analysis_type"], "analysis_evidence.analysis_type"),
            run_etag=_required(item["run_etag"], "analysis_evidence.run_etag"),
            input_digest=_required(item["input_digest"], "analysis_evidence.input_digest"),
        )
        for item in analysis_evidence
    )
    if len({item.run_id for item in evidence}) != len(evidence):
        raise DmaicInputError("duplicate_analysis_evidence", "Analysis evidence Run IDs must be unique.", "analysis_evidence")
    sources = tuple(item for item in (
        project.root_cause_analysis, project.problem_definition, project.measurement_plan,
        project.sipoc, project.charter,
    ) if item is not None)
    selection = DmaicSolutionSelection(
        document_id=f"{project.project_id}-solution-selection-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        problem_statement=_required(problem_statement, "problem_statement"),
        candidate_solutions=candidates, selected_solution=selected,
        decision_rationale=_required(decision_rationale, "decision_rationale"),
        validation_plan=_required(validation_plan, "validation_plan"),
        source_documents=sources, analysis_evidence=evidence,
        actor=_required(actor, "actor"), occurred_at=_required(occurred_at, "occurred_at"),
    )
    selection = replace(selection, digest=_solution_selection_digest(selection))
    reference = DmaicDocumentReference("solution_selection", selection.document_id, selection.revision, selection.digest)
    revised = replace(project, revision=project.revision + 1, parent_digest=project.digest, digest="", solution_selection=reference)
    return replace(revised, digest=_project_digest(revised)), selection


def save_pilot_plan(
    project: DmaicProject,
    *,
    pilot_type: str,
    scope: str,
    study_design: str,
    sample_plan: str,
    duration: str,
    success_metrics: tuple[str, ...],
    stop_criteria: tuple[str, ...],
    risk_responses: tuple[str, ...],
    analysis_evidence: tuple[dict[str, str], ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicPilotPlan]:
    """Save a pilot plan without claiming that the planned pilot has run."""
    previous = project.pilot_plan
    revision = 1 if previous is None else previous.revision + 1
    evidence = tuple(
        DmaicAnalysisEvidenceReference(
            run_id=_required(item["run_id"], "analysis_evidence.run_id"),
            analysis_type=_required(item["analysis_type"], "analysis_evidence.analysis_type"),
            run_etag=_required(item["run_etag"], "analysis_evidence.run_etag"),
            input_digest=_required(item["input_digest"], "analysis_evidence.input_digest"),
        )
        for item in analysis_evidence
    )
    if len({item.run_id for item in evidence}) != len(evidence):
        raise DmaicInputError("duplicate_analysis_evidence", "Analysis evidence Run IDs must be unique.", "analysis_evidence")
    sources = tuple(item for item in (
        project.solution_selection, project.root_cause_analysis, project.problem_definition,
        project.measurement_plan, project.sipoc, project.charter,
    ) if item is not None)
    plan = DmaicPilotPlan(
        document_id=f"{project.project_id}-pilot-plan-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        pilot_type=_choice(pilot_type, {"before_after", "controlled_trial", "doe_confirmation"}, "pilot_type"),
        scope=_required(scope, "scope"), study_design=_required(study_design, "study_design"),
        sample_plan=_required(sample_plan, "sample_plan"), duration=_required(duration, "duration"),
        success_metrics=_items(success_metrics, "success_metrics"),
        stop_criteria=_items(stop_criteria, "stop_criteria"), risk_responses=_items(risk_responses, "risk_responses"),
        source_documents=sources, analysis_evidence=evidence,
        actor=_required(actor, "actor"), occurred_at=_required(occurred_at, "occurred_at"),
    )
    plan = replace(plan, digest=_pilot_plan_digest(plan))
    reference = DmaicDocumentReference("pilot_plan", plan.document_id, plan.revision, plan.digest)
    revised = replace(project, revision=project.revision + 1, parent_digest=project.digest, digest="", pilot_plan=reference)
    return replace(revised, digest=_project_digest(revised)), plan


def save_control_handoff(
    project: DmaicProject,
    *,
    monitoring_plan: str,
    review_frequency: str,
    effectiveness_criteria: tuple[str, ...],
    reaction_plans: tuple[dict[str, str | None], ...],
    fmea_control_plan: dict[str, object],
    analysis_evidence: tuple[dict[str, str], ...],
    actor: str,
    occurred_at: str,
) -> tuple[DmaicProject, DmaicControlHandoff]:
    """Save a Control-phase operating contract with immutable evidence identities."""
    previous = project.control_handoff
    revision = 1 if previous is None else previous.revision + 1
    evidence = tuple(
        DmaicAnalysisEvidenceReference(
            run_id=_required(item["run_id"], "analysis_evidence.run_id"),
            analysis_type=_required(item["analysis_type"], "analysis_evidence.analysis_type"),
            run_etag=_required(item["run_etag"], "analysis_evidence.run_etag"),
            input_digest=_required(item["input_digest"], "analysis_evidence.input_digest"),
        )
        for item in analysis_evidence
    )
    if not evidence:
        raise DmaicInputError("analysis_evidence_required", "At least one SPC or capability Run is required.", "analysis_evidence")
    if len({item.run_id for item in evidence}) != len(evidence):
        raise DmaicInputError("duplicate_analysis_evidence", "Analysis evidence Run IDs must be unique.", "analysis_evidence")
    if any(
        not (
            item.analysis_type.startswith("spc.")
            or item.analysis_type.startswith("capability.")
        )
        for item in evidence
    ):
        raise DmaicInputError(
            "unsupported_control_evidence",
            "Control handoff accepts only SPC or capability analysis Runs.",
            "analysis_evidence",
        )
    reactions = tuple(
        DmaicReactionPlanItem(
            trigger=_required(str(item["trigger"]), "reaction_plans.trigger"),
            action=_required(str(item["action"]), "reaction_plans.action"),
            owner_ref=_required(str(item["owner_ref"]), "reaction_plans.owner_ref"),
            escalation_ref=_optional(item.get("escalation_ref")),
            response_time=_required(str(item["response_time"]), "reaction_plans.response_time"),
        )
        for item in reaction_plans
    )
    if not reactions:
        raise DmaicInputError("reaction_plan_required", "At least one reaction plan is required.", "reaction_plans")
    control_ids = _items(
        tuple(str(value) for value in fmea_control_plan["control_ids"]),  # type: ignore[index]
        "fmea_control_plan.control_ids",
    )
    if not control_ids:
        raise DmaicInputError(
            "fmea_control_required",
            "At least one FMEA control-plan item is required.",
            "fmea_control_plan.control_ids",
        )
    fmea = DmaicFmeaControlPlanReference(
        study_id=_required(str(fmea_control_plan["study_id"]), "fmea_control_plan.study_id"),
        study_etag=_required(str(fmea_control_plan["study_etag"]), "fmea_control_plan.study_etag"),
        study_digest=_required(str(fmea_control_plan["study_digest"]), "fmea_control_plan.study_digest"),
        control_ids=control_ids,
    )
    sources = tuple(item for item in (
        project.pilot_plan, project.solution_selection, project.root_cause_analysis,
        project.measurement_plan, project.problem_definition, project.stakeholder_assessment,
        project.sipoc, project.voice_of_customer, project.charter,
    ) if item is not None)
    criteria = _items(effectiveness_criteria, "effectiveness_criteria")
    if not criteria:
        raise DmaicInputError(
            "effectiveness_criteria_required",
            "At least one effectiveness criterion is required.",
            "effectiveness_criteria",
        )
    handoff = DmaicControlHandoff(
        document_id=f"{project.project_id}-control-handoff-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        monitoring_plan=_required(monitoring_plan, "monitoring_plan"),
        review_frequency=_required(review_frequency, "review_frequency"),
        effectiveness_criteria=criteria,
        reaction_plans=reactions, source_documents=sources, fmea_control_plan=fmea,
        analysis_evidence=evidence, actor=_required(actor, "actor"), occurred_at=_required(occurred_at, "occurred_at"),
    )
    handoff = replace(handoff, digest=_control_handoff_digest(handoff))
    reference = DmaicDocumentReference("control_handoff", handoff.document_id, handoff.revision, handoff.digest)
    revised = replace(project, revision=project.revision + 1, parent_digest=project.digest, digest="", control_handoff=reference)
    return replace(revised, digest=_project_digest(revised)), handoff
