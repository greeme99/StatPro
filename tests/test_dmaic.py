from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.dmaic import (
    DmaicCharter,
    DmaicProject,
    DmaicSipocMap,
    DmaicVoiceOfCustomerStudy,
    create_project,
    save_charter,
    save_sipoc,
    save_voice_of_customer,
)


class DmaicProjectTests(unittest.TestCase):
    def test_charter_revisions_are_immutable_and_project_keeps_only_reference(self) -> None:
        project = create_project(
            project_id="DMAIC-001", title="Connector yield", owner_ref="quality.engineer"
        )
        first_project, first = save_charter(
            project,
            business_case="Reduce scrap cost",
            problem_statement="Connector insertion failures exceed target.",
            scope_in=("Assembly",), scope_out=("Supplier process",),
            success_metrics=("First pass yield",), team_refs=("quality.engineer",),
            budget="5000000 KRW", milestones=("Measure by 2026-11-01",),
            risk_refs=("RISK-001",), assumptions_constraints=("Line availability",),
            actor="quality.engineer", occurred_at="2026-10-30T09:00:00+09:00",
        )
        second_project, second = save_charter(
            first_project,
            business_case="Reduce scrap and rework cost",
            problem_statement="Connector insertion failures exceed target.",
            scope_in=("Assembly",), scope_out=("Supplier process",),
            success_metrics=("First pass yield",), team_refs=("quality.engineer",),
            budget="6000000 KRW", milestones=("Measure by 2026-11-01",),
            risk_refs=("RISK-001",), assumptions_constraints=("Line availability",),
            actor="quality.engineer", occurred_at="2026-10-30T10:00:00+09:00",
        )

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(first.business_case, "Reduce scrap cost")
        self.assertEqual(second_project.parent_digest, first_project.digest)
        self.assertEqual(second_project.charter.document_id, second.document_id)
        self.assertNotIn("business_case", second_project.to_dict())
        self.assertEqual(DmaicProject.from_dict(second_project.to_dict()), second_project)
        self.assertEqual(DmaicCharter.from_dict(first.to_dict()), first)

    def test_voice_of_customer_revisions_are_immutable_and_project_keeps_only_reference(self) -> None:
        project = create_project(
            project_id="DMAIC-002", title="Connector yield", owner_ref="quality.engineer"
        )
        first_project, first = save_voice_of_customer(
            project,
            collection_plan="Interview assembly operators weekly.",
            data_points=("VOC-001",), requirements=("Stable connector insertion",),
            pain_points=("Intermittent insertion failures",), opportunities=("Guide pin trial",),
            actions=("Validate guide pin",), recommendations=("Run pilot",),
            next_steps=("Review pilot evidence",), actor="quality.engineer",
            occurred_at="2026-10-30T09:00:00+09:00",
        )
        second_project, second = save_voice_of_customer(
            first_project,
            collection_plan="Interview assembly operators daily.",
            data_points=("VOC-001", "VOC-002"), requirements=("Stable connector insertion",),
            pain_points=("Intermittent insertion failures",), opportunities=("Guide pin trial",),
            actions=("Validate guide pin",), recommendations=("Run pilot",),
            next_steps=("Review pilot evidence",), actor="quality.engineer",
            occurred_at="2026-10-30T10:00:00+09:00",
        )

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(first.collection_plan, "Interview assembly operators weekly.")
        self.assertEqual(second_project.voice_of_customer.document_id, second.document_id)
        self.assertNotIn("collection_plan", second_project.to_dict())
        self.assertEqual(DmaicVoiceOfCustomerStudy.from_dict(first.to_dict()), first)

    def test_sipoc_revisions_are_immutable_and_project_keeps_only_reference(self) -> None:
        project = create_project(
            project_id="DMAIC-003", title="Connector yield", owner_ref="quality.engineer"
        )
        first_project, first = save_sipoc(
            project,
            process_start_boundary="Receive connector", process_end_boundary="Pack assembly",
            suppliers=("Connector supplier",), inputs=("Connector",),
            process_steps=("Inspect", "Insert", "Test"), outputs=("Verified assembly",),
            customers=("Final assembly",), actor="quality.engineer",
            occurred_at="2026-10-30T09:00:00+09:00",
        )
        second_project, second = save_sipoc(
            first_project,
            process_start_boundary="Receive connector", process_end_boundary="Pack assembly",
            suppliers=("Connector supplier", "Fixture supplier"), inputs=("Connector", "Fixture"),
            process_steps=("Inspect", "Insert", "Test"), outputs=("Verified assembly",),
            customers=("Final assembly",), actor="quality.engineer",
            occurred_at="2026-10-30T10:00:00+09:00",
        )

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(first.suppliers, ("Connector supplier",))
        self.assertEqual(second_project.sipoc.document_id, second.document_id)
        self.assertNotIn("process_steps", second_project.to_dict())
        self.assertEqual(DmaicSipocMap.from_dict(first.to_dict()), first)


if __name__ == "__main__":
    unittest.main()
