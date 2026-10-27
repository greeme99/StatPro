"""Read-only, versioned FMEA review report projected from one study snapshot."""

from __future__ import annotations

from typing import Any

from statpro.fmea.models import FmeaStudySnapshot


def build_study_report(study: FmeaStudySnapshot) -> dict[str, Any]:
    """Join owned IDs for a reviewable report without changing the study."""

    steps = {step.step_id: step for step in study.process_steps}
    characteristics = {item.characteristic_id: item for item in study.characteristics}
    controls_by_failure: dict[str, list[dict[str, Any]]] = {}
    for control in study.control_plan_items:
        for failure_id in control.failure_item_ids:
            controls_by_failure.setdefault(failure_id, []).append(control.to_dict())
    actions_by_failure: dict[str, list[dict[str, Any]]] = {}
    for action in study.actions:
        actions_by_failure.setdefault(action.item_id, []).append(action.to_dict())

    rows: list[dict[str, Any]] = []
    for item in study.items:
        step = steps.get(item.process_step_id) if item.process_step_id else None
        rows.append(
            {
                "failure": item.to_dict(),
                "process_step": step.to_dict() if step else None,
                "characteristics": [
                    characteristics[identifier].to_dict()
                    for identifier in item.characteristic_ids
                    if identifier in characteristics
                ],
                "control_plan_items": controls_by_failure.get(item.item_id, []),
                "actions": actions_by_failure.get(item.item_id, []),
            }
        )

    approval = next(
        (event for event in reversed(study.audit_events) if event.event_type == "study_approved"),
        None,
    )
    return {
        "report_type": "statpro.fmea.study_review.v1",
        "study_id": study.study_id,
        "study_name": study.name,
        "study_type": study.study_type.value,
        "standard_version": study.standard_version,
        "revision": study.revision,
        "snapshot_digest": study.digest,
        "status": study.status.value,
        "action_priority_policy": {
            "policy_id": study.action_priority_policy_id,
            "policy_digest": study.action_priority_policy_digest,
        },
        "seven_step_progress": [step.to_dict() for step in study.seven_step_progress],
        "rows": rows,
        "approval_record": (
            {"actor": approval.actor, "occurred_at": approval.occurred_at,
             "audit_sequence": approval.sequence}
            if approval else None
        ),
        "audit_events": [
            {"sequence": event.sequence, "event_type": event.event_type,
             "actor": event.actor, "occurred_at": event.occurred_at,
             "details": event.details}
            for event in study.audit_events
        ],
        "limitations": [
            "Actor names are self-reported workflow fields, not authenticated electronic signatures.",
            "Stored SPC/MSA Runs were verified when linked; this report does not recheck their availability or content.",
        ],
    }
