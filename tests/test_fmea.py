from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.fmea import (
    ActionPriorityEntry,
    ActionPriorityPolicy,
    FmeaInputError,
    RiskRatings,
    StepStatus,
    StudyStatus,
    StudyType,
    add_failure_analysis,
    add_recommended_action,
    approve_study,
    complete_action,
    create_fmea_study,
    submit_for_review,
)

NOW = "2026-10-19T10:00:00+09:00"


def policy(version: str = "licensed-standard-2026") -> ActionPriorityPolicy:
    return ActionPriorityPolicy(
        policy_id="customer-ap-matrix",
        standard_version=version,
        entries=(ActionPriorityEntry(8, 4, 5, "H"), ActionPriorityEntry(8, 2, 2, "M")),
    )


def study_with_item():
    study = create_fmea_study(
        study_id="PFMEA-001",
        name="Assembly Process",
        study_type=StudyType.PROCESS,
        standard_version="licensed-standard-2026",
        actor="quality.engineer",
        occurred_at=NOW,
    )
    return add_failure_analysis(
        study,
        item_id="FA-001",
        structure_element="Connector assembly",
        function="Maintain electrical contact",
        requirement="Contact resistance within specification",
        failure_mode="Incomplete insertion",
        effect="Intermittent open circuit",
        cause="Fixture alignment drift",
        prevention_control="Fixture setup checklist",
        detection_control="End-of-line continuity test",
        ratings=RiskRatings(8, 4, 5),
        actor="quality.engineer",
        occurred_at=NOW,
        policy=policy(),
    )


class FmeaValueObjectTests(unittest.TestCase):
    def test_risk_ratings_calculate_rpn_and_reject_values_outside_one_to_ten(self) -> None:
        self.assertEqual(RiskRatings(8, 4, 5).rpn, 160)
        with self.assertRaises(FmeaInputError) as context:
            RiskRatings(11, 4, 5)
        self.assertEqual(context.exception.detail.code, "invalid_risk_rating")

    def test_action_priority_policy_is_external_versioned_and_deterministic(self) -> None:
        first = policy()
        second = ActionPriorityPolicy(
            policy_id="customer-ap-matrix",
            standard_version="licensed-standard-2026",
            entries=tuple(reversed(first.entries)),
        )
        self.assertEqual(first.evaluate(RiskRatings(8, 4, 5)), "H")
        self.assertIsNone(first.evaluate(RiskRatings(1, 1, 1)))
        self.assertEqual(first.digest, second.digest)


class FmeaWorkflowTests(unittest.TestCase):
    def test_seven_step_progress_is_derived_from_owned_study_evidence(self) -> None:
        initial = create_fmea_study(
            study_id="PFMEA-STEPS",
            name="Assembly Process",
            study_type=StudyType.PROCESS,
            standard_version="licensed-standard-2026",
            actor="quality.engineer",
            occurred_at=NOW,
        )
        self.assertEqual(len(initial.seven_step_progress), 7)
        self.assertEqual(initial.seven_step_progress[0].status, StepStatus.COMPLETE)
        self.assertTrue(
            all(
                step.status == StepStatus.NOT_STARTED
                for step in initial.seven_step_progress[1:]
            )
        )

        analyzed = study_with_item()
        self.assertTrue(
            all(
                step.status == StepStatus.COMPLETE
                for step in analyzed.seven_step_progress[1:5]
            )
        )
        self.assertEqual(analyzed.seven_step_progress[5].status, StepStatus.NOT_STARTED)

        legacy_payload = initial.to_dict()
        legacy_payload.pop("seven_step_progress")
        restored = type(initial).from_dict(legacy_payload)
        self.assertEqual(len(restored.to_dict()["seven_step_progress"]), 7)

    def test_adding_failure_analysis_creates_revision_and_preserves_parent(self) -> None:
        initial = create_fmea_study(
            study_id="PFMEA-001",
            name="Assembly Process",
            study_type=StudyType.PROCESS,
            standard_version="licensed-standard-2026",
            actor="quality.engineer",
            occurred_at=NOW,
        )
        revised = study_with_item()

        self.assertEqual(initial.revision, 1)
        self.assertEqual(initial.items, ())
        self.assertEqual(revised.revision, 2)
        self.assertEqual(revised.parent_digest, initial.digest)
        self.assertEqual(revised.items[0].initial_ratings.rpn, 160)
        self.assertEqual(revised.items[0].action_priority, "H")
        self.assertIsNone(revised.items[0].action_priority_reason)
        self.assertEqual(revised.action_priority_policy_digest, policy().digest)

    def test_policy_standard_must_match_study_standard(self) -> None:
        study = create_fmea_study(
            study_id="PFMEA-001",
            name="Assembly Process",
            study_type=StudyType.PROCESS,
            standard_version="standard-a",
            actor="quality.engineer",
            occurred_at=NOW,
        )
        with self.assertRaises(FmeaInputError) as context:
            add_failure_analysis(
                study,
                item_id="FA-001",
                structure_element="Assembly",
                function="Connect",
                requirement="Conduct",
                failure_mode="Open",
                effect="No signal",
                cause="Misalignment",
                prevention_control="Fixture",
                detection_control="Test",
                ratings=RiskRatings(8, 4, 5),
                actor="quality.engineer",
                occurred_at=NOW,
                policy=policy("standard-b"),
            )
        self.assertEqual(context.exception.detail.code, "action_priority_standard_mismatch")

    def test_completed_action_preserves_initial_and_records_revised_risk(self) -> None:
        study = add_recommended_action(
            study_with_item(),
            action_id="ACT-001",
            item_id="FA-001",
            description="Add fixture alignment sensor",
            owner="process.engineer",
            due_date="2026-11-01",
            actor="quality.engineer",
            occurred_at=NOW,
        )
        completed = complete_action(
            study,
            action_id="ACT-001",
            result="Sensor installed and verified",
            evidence_refs=("evidence://validation/fixture-001",),
            revised_ratings=RiskRatings(8, 2, 2),
            actor="process.engineer",
            occurred_at="2026-10-20T10:00:00+09:00",
            policy=policy(),
        )

        self.assertEqual(study.actions[0].status.value, "open")
        self.assertEqual(completed.actions[0].status.value, "complete")
        self.assertEqual(completed.items[0].initial_ratings.rpn, 160)
        self.assertEqual(completed.items[0].current_ratings.rpn, 32)
        self.assertEqual(completed.items[0].action_priority, "M")

    def test_open_actions_block_approval(self) -> None:
        study = add_recommended_action(
            study_with_item(),
            action_id="ACT-001",
            item_id="FA-001",
            description="Add fixture alignment sensor",
            owner="process.engineer",
            due_date="2026-11-01",
            actor="quality.engineer",
            occurred_at=NOW,
        )
        in_review = submit_for_review(study, actor="reviewer", occurred_at=NOW)
        with self.assertRaises(FmeaInputError) as context:
            approve_study(in_review, actor="approver", occurred_at=NOW)
        self.assertEqual(context.exception.detail.code, "open_actions_block_approval")

    def test_completed_study_can_be_reviewed_and_approved_with_audit_history(self) -> None:
        study = add_recommended_action(
            study_with_item(),
            action_id="ACT-001",
            item_id="FA-001",
            description="Add fixture alignment sensor",
            owner="process.engineer",
            due_date="2026-11-01",
            actor="quality.engineer",
            occurred_at=NOW,
        )
        study = complete_action(
            study,
            action_id="ACT-001",
            result="Verified",
            evidence_refs=(),
            revised_ratings=RiskRatings(8, 2, 2),
            actor="process.engineer",
            occurred_at=NOW,
            policy=policy(),
        )
        study = submit_for_review(study, actor="reviewer", occurred_at=NOW)
        approved = approve_study(study, actor="approver", occurred_at=NOW)

        self.assertEqual(approved.status, StudyStatus.APPROVED)
        self.assertEqual(approved.revision, 6)
        self.assertEqual(
            [event.sequence for event in approved.audit_events], [1, 2, 3, 4, 5, 6]
        )
        self.assertEqual(approved.audit_events[-1].event_type, "study_approved")
        self.assertEqual(approved.seven_step_progress[5].status, StepStatus.COMPLETE)
        self.assertEqual(approved.seven_step_progress[6].status, StepStatus.COMPLETE)
        self.assertEqual(approved.to_dict()["seven_step_progress"][6]["status"], "complete")
