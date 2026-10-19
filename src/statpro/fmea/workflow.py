"""State transitions for immutable FMEA study revisions."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from typing import Any

from statpro.domain.identity import input_digest
from statpro.fmea.models import (
    ActionPriorityPolicy,
    ActionStatus,
    AuditEvent,
    FailureAnalysis,
    FmeaInputError,
    FmeaStudySnapshot,
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
    )
    return replace(revised, digest=_snapshot_digest(revised))


def _require_draft(study: FmeaStudySnapshot) -> None:
    if study.status != StudyStatus.DRAFT:
        raise FmeaInputError(
            "study_not_editable", "Only draft FMEA studies can be structurally edited.", "status"
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
) -> FmeaStudySnapshot:
    _require_draft(study)
    _validate_policy(study, policy)
    normalized_id = _required(item_id, "item_id")
    if any(item.item_id == normalized_id for item in study.items):
        raise FmeaInputError("duplicate_item_id", "Failure Analysis ID is duplicated.", "item_id")
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
    )
    event = _event(study, "failure_analysis_added", actor, occurred_at, {"item_id": normalized_id})
    return _revise(study, event=event, items=study.items + (item,), policy=policy)


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
