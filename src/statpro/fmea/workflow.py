"""State transitions for immutable FMEA study revisions."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from typing import Any

from statpro.domain.identity import input_digest
from statpro.fmea.models import (
    ActionPriorityPolicy,
    ActionStatus,
    AnalysisEvidenceRef,
    AuditEvent,
    CharacteristicType,
    ControlPlanItem,
    ControlPlanPhase,
    FailureAnalysis,
    FmeaInputError,
    FmeaStudySnapshot,
    ProcessCharacteristic,
    ProcessStep,
    RecommendedAction,
    RiskRatings,
    StudyStatus,
    StudyType,
)


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise FmeaInputError("required_field", f"{field} is required.", field)
    return normalized


def _timestamp(value: str) -> str:
    try:
        return datetime.fromisoformat(value).isoformat()
    except ValueError as error:
        raise FmeaInputError(
            "invalid_timestamp", "occurred_at must be ISO 8601.", "occurred_at"
        ) from error


def _date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise FmeaInputError("invalid_due_date", "due_date must be YYYY-MM-DD.", "due_date") from error


def _snapshot_digest(study: FmeaStudySnapshot) -> str:
    payload = study.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _event(
    study: FmeaStudySnapshot | None,
    event_type: str,
    actor: str,
    occurred_at: str,
    details: dict[str, Any],
) -> AuditEvent:
    return AuditEvent(
        sequence=1 if study is None else len(study.audit_events) + 1,
        event_type=event_type,
        actor=_required(actor, "actor"),
        occurred_at=_timestamp(occurred_at),
        details=details,
    )


def _revise(
    study: FmeaStudySnapshot,
    *,
    event: AuditEvent,
    items: tuple[FailureAnalysis, ...] | None = None,
    actions: tuple[RecommendedAction, ...] | None = None,
    status: StudyStatus | None = None,
    policy: ActionPriorityPolicy | None = None,
    process_steps: tuple[ProcessStep, ...] | None = None,
    characteristics: tuple[ProcessCharacteristic, ...] | None = None,
    control_plan_items: tuple[ControlPlanItem, ...] | None = None,
) -> FmeaStudySnapshot:
    revised = replace(
        study,
        revision=study.revision + 1,
        parent_digest=study.digest,
        digest="",
        items=study.items if items is None else items,
        actions=study.actions if actions is None else actions,
        status=study.status if status is None else status,
        audit_events=study.audit_events + (event,),
        action_priority_policy_id=(
            study.action_priority_policy_id if policy is None else policy.policy_id
        ),
        action_priority_policy_digest=(
            study.action_priority_policy_digest if policy is None else policy.digest
        ),
        action_priority_policy_key=(
            study.action_priority_policy_key if policy is None else policy.policy_key
        ),
        process_steps=study.process_steps if process_steps is None else process_steps,
        characteristics=(
            study.characteristics if characteristics is None else characteristics
        ),
        control_plan_items=(
            study.control_plan_items if control_plan_items is None else control_plan_items
        ),
    )
    return replace(revised, digest=_snapshot_digest(revised))


def _require_draft(study: FmeaStudySnapshot) -> None:
    if study.status != StudyStatus.DRAFT:
        raise FmeaInputError(
            "study_not_editable", "Only draft FMEA studies can be structurally edited.", "status"
        )


def _require_process_study(study: FmeaStudySnapshot) -> None:
    if study.study_type != StudyType.PROCESS:
        raise FmeaInputError(
            "process_traceability_requires_pfmea",
            "Process flow and Control Plan traceability require a Process FMEA Study.",
            "study_type",
        )


def _validate_policy(
    study: FmeaStudySnapshot, policy: ActionPriorityPolicy | None
) -> None:
    if study.action_priority_policy_digest is not None and policy is None:
        raise FmeaInputError(
            "action_priority_policy_required",
            "The Study's Action Priority policy is required when risk ratings change.",
            "policy",
        )
    if policy is not None and policy.standard_version != study.standard_version:
        raise FmeaInputError(
            "action_priority_standard_mismatch",
            "Action Priority policy standard version must match the FMEA study.",
            "policy",
        )
    if (
        policy is not None
        and study.action_priority_policy_digest is not None
        and policy.digest != study.action_priority_policy_digest
    ):
        raise FmeaInputError(
            "action_priority_policy_mismatch",
            "A Study cannot mix different Action Priority policy revisions.",
            "policy",
        )


def _evaluate_priority(
    policy: ActionPriorityPolicy | None, ratings: RiskRatings
) -> tuple[str | None, str | None]:
    if policy is None:
        return None, "policy_not_supplied"
    priority = policy.evaluate(ratings)
    if priority is None:
        return None, "no_matching_entry"
    return priority, None


def create_fmea_study(
    *,
    study_id: str,
    name: str,
    study_type: StudyType,
    standard_version: str,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    event = _event(None, "study_created", actor, occurred_at, {})
    study = FmeaStudySnapshot(
        study_id=_required(study_id, "study_id"),
        name=_required(name, "name"),
        study_type=study_type,
        standard_version=_required(standard_version, "standard_version"),
        status=StudyStatus.DRAFT,
        revision=1,
        parent_digest=None,
        digest="",
        items=(),
        actions=(),
        audit_events=(event,),
    )
    return replace(study, digest=_snapshot_digest(study))


def add_failure_analysis(
    study: FmeaStudySnapshot,
    *,
    item_id: str,
    structure_element: str,
    function: str,
    requirement: str,
    failure_mode: str,
    effect: str,
    cause: str,
    prevention_control: str,
    detection_control: str,
    ratings: RiskRatings,
    actor: str,
    occurred_at: str,
    policy: ActionPriorityPolicy | None = None,
    process_step_id: str | None = None,
    characteristic_ids: tuple[str, ...] = (),
) -> FmeaStudySnapshot:
    _require_draft(study)
    _validate_policy(study, policy)
    normalized_id = _required(item_id, "item_id")
    if any(item.item_id == normalized_id for item in study.items):
        raise FmeaInputError("duplicate_item_id", "Failure Analysis ID is duplicated.", "item_id")
    normalized_step_id = None if process_step_id is None else _required(process_step_id, "process_step_id")
    normalized_characteristic_ids = tuple(
        dict.fromkeys(_required(value, "characteristic_ids") for value in characteristic_ids)
    )
    if study.process_steps and normalized_step_id is None:
        raise FmeaInputError(
            "process_step_required",
            "Failure Analysis must reference a Process Step when a process flow exists.",
            "process_step_id",
        )
    if normalized_step_id is not None and not any(
        step.step_id == normalized_step_id for step in study.process_steps
    ):
        raise FmeaInputError(
            "unknown_process_step", "Failure Analysis references an unknown Process Step.", "process_step_id"
        )
    characteristic_by_id = {
        item.characteristic_id: item for item in study.characteristics
    }
    for characteristic_id in normalized_characteristic_ids:
        characteristic = characteristic_by_id.get(characteristic_id)
        if characteristic is None:
            raise FmeaInputError(
                "unknown_characteristic",
                "Failure Analysis references an unknown Process Characteristic.",
                "characteristic_ids",
            )
        if normalized_step_id != characteristic.process_step_id:
            raise FmeaInputError(
                "characteristic_step_mismatch",
                "Failure Analysis and Process Characteristic must reference the same Process Step.",
                "characteristic_ids",
            )
    action_priority, action_priority_reason = _evaluate_priority(policy, ratings)
    item = FailureAnalysis(
        item_id=normalized_id,
        structure_element=_required(structure_element, "structure_element"),
        function=_required(function, "function"),
        requirement=_required(requirement, "requirement"),
        failure_mode=_required(failure_mode, "failure_mode"),
        effect=_required(effect, "effect"),
        cause=_required(cause, "cause"),
        prevention_control=_required(prevention_control, "prevention_control"),
        detection_control=_required(detection_control, "detection_control"),
        initial_ratings=ratings,
        current_ratings=ratings,
        action_priority=action_priority,
        action_priority_reason=action_priority_reason,
        process_step_id=normalized_step_id,
        characteristic_ids=normalized_characteristic_ids,
    )
    event = _event(study, "failure_analysis_added", actor, occurred_at, {"item_id": normalized_id})
    return _revise(study, event=event, items=study.items + (item,), policy=policy)


def add_process_step(
    study: FmeaStudySnapshot,
    *,
    step_id: str,
    sequence: int,
    name: str,
    operation: str,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    _require_draft(study)
    _require_process_study(study)
    normalized_id = _required(step_id, "step_id")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise FmeaInputError(
            "invalid_process_step_sequence",
            "Process Step sequence must be a positive integer.",
            "sequence",
        )
    if any(step.step_id == normalized_id for step in study.process_steps):
        raise FmeaInputError("duplicate_process_step_id", "Process Step ID is duplicated.", "step_id")
    if any(step.sequence == sequence for step in study.process_steps):
        raise FmeaInputError(
            "duplicate_process_step_sequence",
            "Process Step sequence is duplicated.",
            "sequence",
        )
    step = ProcessStep(
        step_id=normalized_id,
        sequence=sequence,
        name=_required(name, "name"),
        operation=_required(operation, "operation"),
    )
    steps = tuple(sorted(study.process_steps + (step,), key=lambda item: item.sequence))
    event = _event(
        study,
        "process_step_added",
        actor,
        occurred_at,
        {"step_id": normalized_id, "sequence": sequence},
    )
    return _revise(study, event=event, process_steps=steps)


def add_process_characteristic(
    study: FmeaStudySnapshot,
    *,
    characteristic_id: str,
    process_step_id: str,
    name: str,
    characteristic_type: CharacteristicType,
    specification: str,
    special_classification: str | None,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    _require_draft(study)
    _require_process_study(study)
    normalized_id = _required(characteristic_id, "characteristic_id")
    normalized_step_id = _required(process_step_id, "process_step_id")
    if any(item.characteristic_id == normalized_id for item in study.characteristics):
        raise FmeaInputError(
            "duplicate_characteristic_id",
            "Process Characteristic ID is duplicated.",
            "characteristic_id",
        )
    if not any(step.step_id == normalized_step_id for step in study.process_steps):
        raise FmeaInputError(
            "unknown_process_step",
            "Process Characteristic references an unknown Process Step.",
            "process_step_id",
        )
    classification = None
    if special_classification is not None and special_classification.strip():
        classification = special_classification.strip()
    characteristic = ProcessCharacteristic(
        characteristic_id=normalized_id,
        process_step_id=normalized_step_id,
        name=_required(name, "name"),
        characteristic_type=characteristic_type,
        specification=_required(specification, "specification"),
        special_classification=classification,
    )
    event = _event(
        study,
        "process_characteristic_added",
        actor,
        occurred_at,
        {"characteristic_id": normalized_id, "process_step_id": normalized_step_id},
    )
    return _revise(
        study,
        event=event,
        characteristics=study.characteristics + (characteristic,),
    )


def add_control_plan_item(
    study: FmeaStudySnapshot,
    *,
    control_id: str,
    phase: ControlPlanPhase,
    characteristic_id: str,
    failure_item_ids: tuple[str, ...],
    measurement_method: str,
    sample_size: int,
    frequency: str,
    control_method: str,
    reaction_plan: str,
    reaction_owner: str,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    _require_draft(study)
    _require_process_study(study)
    normalized_id = _required(control_id, "control_id")
    if any(item.control_id == normalized_id for item in study.control_plan_items):
        raise FmeaInputError("duplicate_control_id", "Control Plan ID is duplicated.", "control_id")
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 1:
        raise FmeaInputError(
            "invalid_control_plan_sample_size",
            "Control Plan sample size must be a positive integer.",
            "sample_size",
        )
    characteristic = next(
        (item for item in study.characteristics if item.characteristic_id == characteristic_id),
        None,
    )
    if characteristic is None:
        raise FmeaInputError(
            "unknown_characteristic",
            "Control Plan references an unknown Process Characteristic.",
            "characteristic_id",
        )
    normalized_failure_ids = tuple(
        dict.fromkeys(_required(value, "failure_item_ids") for value in failure_item_ids)
    )
    if not normalized_failure_ids:
        raise FmeaInputError(
            "control_plan_failure_required",
            "Control Plan item must trace to at least one PFMEA Failure Analysis.",
            "failure_item_ids",
        )
    failures = {item.item_id: item for item in study.items}
    for failure_id in normalized_failure_ids:
        failure = failures.get(failure_id)
        if failure is None:
            raise FmeaInputError(
                "unknown_item", "Control Plan references an unknown Failure Analysis.", "failure_item_ids"
            )
        if (
            failure.process_step_id != characteristic.process_step_id
            or characteristic.characteristic_id not in failure.characteristic_ids
        ):
            raise FmeaInputError(
                "control_plan_traceability_mismatch",
                "Control Plan characteristic must be explicitly linked by each PFMEA Failure Analysis.",
                "failure_item_ids",
            )
    control = ControlPlanItem(
        control_id=normalized_id,
        phase=phase,
        characteristic_id=characteristic.characteristic_id,
        failure_item_ids=normalized_failure_ids,
        measurement_method=_required(measurement_method, "measurement_method"),
        sample_size=sample_size,
        frequency=_required(frequency, "frequency"),
        control_method=_required(control_method, "control_method"),
        reaction_plan=_required(reaction_plan, "reaction_plan"),
        reaction_owner=_required(reaction_owner, "reaction_owner"),
    )
    event = _event(
        study,
        "control_plan_item_added",
        actor,
        occurred_at,
        {
            "control_id": normalized_id,
            "characteristic_id": characteristic.characteristic_id,
            "failure_item_ids": list(normalized_failure_ids),
        },
    )
    return _revise(
        study,
        event=event,
        control_plan_items=study.control_plan_items + (control,),
    )


def link_control_plan_analysis_evidence(
    study: FmeaStudySnapshot,
    *,
    control_id: str,
    reference: AnalysisEvidenceRef,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    """Link a verified immutable SPC/MSA Run to one Control Plan item."""

    _require_draft(study)
    _require_process_study(study)
    control = next(
        (item for item in study.control_plan_items if item.control_id == control_id),
        None,
    )
    if control is None:
        raise FmeaInputError(
            "unknown_control_id", "Control Plan item does not exist.", "control_id"
        )
    if not reference.analysis_type.startswith(("spc.", "msa.")):
        raise FmeaInputError(
            "unsupported_analysis_evidence",
            "Control Plan evidence must be an SPC or MSA analysis Run.",
            "run_id",
        )
    if any(item.run_id == reference.run_id for item in control.analysis_evidence):
        raise FmeaInputError(
            "duplicate_analysis_evidence",
            "This analysis Run is already linked to the Control Plan item.",
            "run_id",
        )
    revised_control = replace(
        control,
        analysis_evidence=control.analysis_evidence + (reference,),
    )
    event = _event(
        study,
        "control_plan_analysis_evidence_linked",
        actor,
        occurred_at,
        {
            "control_id": control_id,
            "run_id": reference.run_id,
            "analysis_type": reference.analysis_type,
            "run_etag": reference.run_etag,
        },
    )
    return _revise(
        study,
        event=event,
        control_plan_items=tuple(
            revised_control if item.control_id == control_id else item
            for item in study.control_plan_items
        ),
    )


def attach_action_priority_policy(
    study: FmeaStudySnapshot,
    *,
    policy: ActionPriorityPolicy,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    """Attach one authorized external policy and reassess existing current ratings."""

    _require_draft(study)
    _validate_policy(study, policy)
    if (
        study.action_priority_policy_digest == policy.digest
        and study.action_priority_policy_key == policy.policy_key
    ):
        raise FmeaInputError(
            "action_priority_policy_already_attached",
            "This Action Priority policy revision is already attached.",
            "policy_key",
        )
    def reassess(item: FailureAnalysis) -> FailureAnalysis:
        priority, reason = _evaluate_priority(policy, item.current_ratings)
        return replace(
            item,
            action_priority=priority,
            action_priority_reason=reason,
        )

    items = tuple(reassess(item) for item in study.items)
    event = _event(
        study,
        "action_priority_policy_attached",
        actor,
        occurred_at,
        {
            "policy_key": policy.policy_key,
            "policy_id": policy.policy_id,
            "policy_digest": policy.digest,
            "standard_version": policy.standard_version,
        },
    )
    return _revise(study, event=event, items=items, policy=policy)


def add_recommended_action(
    study: FmeaStudySnapshot,
    *,
    action_id: str,
    item_id: str,
    description: str,
    owner: str,
    due_date: str,
    actor: str,
    occurred_at: str,
) -> FmeaStudySnapshot:
    _require_draft(study)
    normalized_id = _required(action_id, "action_id")
    if any(action.action_id == normalized_id for action in study.actions):
        raise FmeaInputError("duplicate_action_id", "Action ID is duplicated.", "action_id")
    if not any(item.item_id == item_id for item in study.items):
        raise FmeaInputError("unknown_item", "Action references an unknown Failure Analysis.", "item_id")
    action = RecommendedAction(
        action_id=normalized_id,
        item_id=item_id,
        description=_required(description, "description"),
        owner=_required(owner, "owner"),
        due_date=_date(due_date),
        status=ActionStatus.OPEN,
    )
    event = _event(study, "recommended_action_added", actor, occurred_at, {"action_id": normalized_id})
    return _revise(study, event=event, actions=study.actions + (action,))


def complete_action(
    study: FmeaStudySnapshot,
    *,
    action_id: str,
    result: str,
    evidence_refs: tuple[str, ...],
    revised_ratings: RiskRatings,
    actor: str,
    occurred_at: str,
    policy: ActionPriorityPolicy | None = None,
) -> FmeaStudySnapshot:
    _require_draft(study)
    _validate_policy(study, policy)
    matches = [action for action in study.actions if action.action_id == action_id]
    if not matches:
        raise FmeaInputError("unknown_action", "Action ID does not exist.", "action_id")
    action = matches[0]
    if action.status == ActionStatus.COMPLETE:
        raise FmeaInputError("action_already_complete", "Action is already complete.", "action_id")
    completed_action = replace(
        action,
        status=ActionStatus.COMPLETE,
        result=_required(result, "result"),
        evidence_refs=tuple(_required(reference, "evidence_refs") for reference in evidence_refs),
    )
    actions = tuple(completed_action if candidate.action_id == action_id else candidate for candidate in study.actions)
    items = tuple(
        replace(
            item,
            current_ratings=revised_ratings,
            action_priority=(
                item.action_priority
                if policy is None
                else _evaluate_priority(policy, revised_ratings)[0]
            ),
            action_priority_reason=(
                item.action_priority_reason
                if policy is None
                else _evaluate_priority(policy, revised_ratings)[1]
            ),
        )
        if item.item_id == action.item_id
        else item
        for item in study.items
    )
    event = _event(
        study,
        "recommended_action_completed",
        actor,
        occurred_at,
        {"action_id": action_id, "item_id": action.item_id},
    )
    return _revise(study, event=event, items=items, actions=actions, policy=policy)


def submit_for_review(
    study: FmeaStudySnapshot, *, actor: str, occurred_at: str
) -> FmeaStudySnapshot:
    _require_draft(study)
    if not study.items:
        raise FmeaInputError("empty_study", "A study needs at least one Failure Analysis.", "items")
    event = _event(study, "study_submitted", actor, occurred_at, {})
    return _revise(study, event=event, status=StudyStatus.IN_REVIEW)


def approve_study(
    study: FmeaStudySnapshot, *, actor: str, occurred_at: str
) -> FmeaStudySnapshot:
    if study.status != StudyStatus.IN_REVIEW:
        raise FmeaInputError(
            "study_not_in_review", "Only an in-review study can be approved.", "status"
        )
    open_actions = [
        action.action_id
        for action in study.actions
        if action.status not in {ActionStatus.COMPLETE, ActionStatus.CANCELLED}
    ]
    if open_actions:
        raise FmeaInputError(
            "open_actions_block_approval",
            f"Complete or cancel actions before approval: {', '.join(open_actions)}.",
            "actions",
        )
    event = _event(study, "study_approved", actor, occurred_at, {})
    return _revise(study, event=event, status=StudyStatus.APPROVED)
