from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.dmaic import (
    DmaicCharter,
    DmaicControlHandoff,
    DmaicInputError,
    DmaicMeasurementPlan,
    DmaicProblemDefinition,
    DmaicProject,
    DmaicSipocMap,
    DmaicStakeholderAssessment,
    DmaicVoiceOfCustomerStudy,
    create_project,
    save_charter,
    save_control_handoff,
    save_measurement_plan,
    save_pilot_plan,
    save_problem_definition,
    save_root_cause_analysis,
    save_sipoc,
    save_solution_selection,
    save_stakeholder_assessment,
    save_voice_of_customer,
)


class DmaicProjectTests(unittest.TestCase):
    def test_control_handoff_snapshots_fmea_and_control_run_evidence(self) -> None:
        project = create_project(
            project_id="DMAIC-CONTROL", title="Connector yield", owner_ref="quality.engineer"
        )
        project, selection = save_solution_selection(
            project,
            problem_statement="Connector defect rate increased",
            candidate_solutions=("Set torque window",),
            selected_solution="Set torque window",
            decision_rationale="Lowest setup risk.",
            validation_plan="Validate with a blocked DOE.",
            analysis_evidence=(),
            actor="quality.engineer",
            occurred_at="2026-11-05T10:00:00+09:00",
        )
        revised, handoff = save_control_handoff(
            project,
            monitoring_plan="Review the Xbar-R chart at the end of every shift.",
            review_frequency="Every shift",
            effectiveness_criteria=("No Rule 1 signal for 20 subgroups",),
            reaction_plans=({
                "trigger": "Any Rule 1 signal",
                "action": "Stop the line and quarantine the current lot",
                "owner_ref": "line.supervisor",
                "escalation_ref": "quality.manager",
                "response_time": "Within 15 minutes",
            },),
            fmea_control_plan={
                "study_id": "PFMEA-001",
                "study_etag": "fmea-etag-001",
                "study_digest": "f" * 64,
                "control_ids": ("CP-001",),
            },
            analysis_evidence=({
                "run_id": "spc-xbar-r-001",
                "analysis_type": "spc.xbar_r",
                "run_etag": "run-etag-001",
                "input_digest": "a" * 64,
            },),
            actor="quality.engineer",
            occurred_at="2026-11-05T11:00:00+09:00",
        )

        self.assertEqual(revised.control_handoff.document_id, handoff.document_id)
        self.assertEqual(handoff.source_documents[0].document_id, selection.document_id)
        self.assertEqual(handoff.fmea_control_plan.control_ids, ("CP-001",))
        self.assertEqual(handoff.analysis_evidence[0].run_id, "spc-xbar-r-001")
        self.assertEqual(DmaicControlHandoff.from_dict(handoff.to_dict()), handoff)

    def test_control_handoff_rejects_non_control_evidence(self) -> None:
        project = create_project(
            project_id="DMAIC-CONTROL-INVALID",
            title="Connector yield",
            owner_ref="quality.engineer",
        )

        with self.assertRaisesRegex(DmaicInputError, "only SPC or capability"):
            save_control_handoff(
                project,
                monitoring_plan="Review every shift.",
                review_frequency="Every shift",
                effectiveness_criteria=("Cpk above 1.33",),
                reaction_plans=({
                    "trigger": "Cpk below 1.33",
                    "action": "Open a containment action",
                    "owner_ref": "quality.engineer",
                    "escalation_ref": None,
                    "response_time": "Within one shift",
                },),
                fmea_control_plan={
                    "study_id": "PFMEA-001",
                    "study_etag": "fmea-etag-001",
                    "study_digest": "f" * 64,
                    "control_ids": ("CP-001",),
                },
                analysis_evidence=({
                    "run_id": "doe-001",
                    "analysis_type": "doe.full_factorial",
                    "run_etag": "run-etag-001",
                    "input_digest": "a" * 64,
                },),
                actor="quality.engineer",
                occurred_at="2026-11-05T11:00:00+09:00",
            )

    def test_pilot_plan_snapshots_solution_selection_and_evidence(self) -> None:
        project = create_project(
            project_id="DMAIC-PILOT", title="Connector yield", owner_ref="quality.engineer"
        )
        project, selection = save_solution_selection(
            project,
            problem_statement="Connector defect rate increased",
            candidate_solutions=("Set torque window",),
            selected_solution="Set torque window",
            decision_rationale="Lowest setup risk.",
            validation_plan="Validate with a blocked DOE.",
            analysis_evidence=(),
            actor="quality.engineer",
            occurred_at="2026-11-05T10:00:00+09:00",
        )
        revised, plan = save_pilot_plan(
            project,
            pilot_type="doe_confirmation",
            scope="Line 2 assembly",
            study_design="Blocked DOE confirmation",
            sample_plan="30 units per condition",
            duration="Two shifts",
            success_metrics=("Defect rate below 1%",),
            stop_criteria=("Safety incident",),
            risk_responses=("Stop and restore the prior setting",),
            analysis_evidence=({
                "run_id": "doe-002", "analysis_type": "doe.full_factorial",
                "run_etag": "run-etag", "input_digest": "c" * 64,
            },),
            actor="quality.engineer",
            occurred_at="2026-11-05T10:05:00+09:00",
        )
        self.assertEqual(revised.pilot_plan.document_id, plan.document_id)
        self.assertEqual(plan.source_documents[0].document_id, selection.document_id)
        self.assertEqual(plan.analysis_evidence[0].run_id, "doe-002")
        self.assertEqual(type(plan).from_dict(plan.to_dict()), plan)

    def test_solution_selection_snapshots_root_cause_and_doe_evidence(self) -> None:
        project = create_project(
            project_id="DMAIC-IMPROVE", title="Connector yield", owner_ref="quality.engineer"
        )
        project, definition = save_problem_definition(
            project, problem_statement="Connector defect rate increased", impact="Scrap cost",
            current_state="4.2%", target_state="1.0%", timeframe="Q4", location_scope="Line 2",
            severity="high", urgency="high", objectives=("Verify causes",),
            actor="quality.engineer", occurred_at="2026-11-04T10:00:00+09:00",
        )
        project, analysis = save_root_cause_analysis(
            project, problem_statement=definition.problem_statement, method="fishbone_pareto",
            candidate_causes=("Torque variation",), verified_causes=("Torque variation",),
            next_actions=("Run DOE",), analysis_evidence=(), actor="quality.engineer",
            occurred_at="2026-11-04T10:05:00+09:00",
        )
        revised, selection = save_solution_selection(
            project, problem_statement=analysis.problem_statement,
            candidate_solutions=("Set torque window", "Add fixture guide"),
            selected_solution="Set torque window", decision_rationale="Lowest setup risk.",
            validation_plan="Validate with a blocked DOE.", analysis_evidence=({
                "run_id": "doe-001", "analysis_type": "doe.full_factorial",
                "run_etag": "run-etag", "input_digest": "b" * 64,
            },), actor="quality.engineer", occurred_at="2026-11-04T10:10:00+09:00",
        )
        self.assertEqual(revised.solution_selection.document_id, selection.document_id)
        self.assertEqual(selection.source_documents[0].document_id, analysis.document_id)
        self.assertEqual(selection.analysis_evidence[0].run_id, "doe-001")
        self.assertEqual(type(selection).from_dict(selection.to_dict()), selection)

    def test_root_cause_analysis_revisions_snapshot_project_and_run_evidence(self) -> None:
        project = create_project(
            project_id="DMAIC-RCA", title="Connector yield", owner_ref="quality.engineer"
        )
        project, definition = save_problem_definition(
            project, problem_statement="Connector defect rate increased", impact="Scrap cost",
            current_state="4.2%", target_state="1.0%", timeframe="Q4", location_scope="Line 2",
            severity="high", urgency="high", objectives=("Verify causes",),
            actor="quality.engineer", occurred_at="2026-11-03T10:00:00+09:00",
        )
        revised, analysis = save_root_cause_analysis(
            project, problem_statement=definition.problem_statement, method="fishbone_pareto",
            candidate_causes=("Torque variation",), verified_causes=("Torque variation",),
            next_actions=("Run DOE",), analysis_evidence=({
                "run_id": "pareto-001", "analysis_type": "quality.pareto",
                "run_etag": "run-etag", "input_digest": "a" * 64,
            },), actor="quality.engineer", occurred_at="2026-11-03T10:05:00+09:00",
        )
        self.assertEqual(revised.root_cause_analysis.document_id, analysis.document_id)
        self.assertEqual(analysis.source_documents[0].document_id, definition.document_id)
        self.assertEqual(analysis.analysis_evidence[0].run_id, "pareto-001")
        self.assertEqual(type(analysis).from_dict(analysis.to_dict()), analysis)

    def test_five_whys_requires_exactly_five_steps_and_preserves_the_chain(self) -> None:
        project = create_project(
            project_id="DMAIC-5WHY", title="Connector yield", owner_ref="quality.engineer"
        )
        steps = (
            "Why 1: Torque was low — setup was not verified.",
            "Why 2: Setup was not verified — checklist was skipped.",
            "Why 3: Checklist was skipped — handoff was incomplete.",
            "Why 4: Handoff was incomplete — ownership was unclear.",
            "Why 5: Ownership was unclear — standard work was missing.",
        )
        revised, analysis = save_root_cause_analysis(
            project, problem_statement="Connector defect rate increased", method="five_whys",
            candidate_causes=("Torque variation",), verified_causes=("Torque variation",),
            next_actions=("Verify standard work",), analysis_evidence=(), actor="quality.engineer",
            occurred_at="2026-11-08T10:05:00+09:00", why_chain=steps,
        )
        self.assertEqual(analysis.why_chain, steps)
        self.assertEqual(revised.root_cause_analysis.document_id, analysis.document_id)
        self.assertEqual(type(analysis).from_dict(analysis.to_dict()), analysis)
        with self.assertRaises(DmaicInputError) as context:
            save_root_cause_analysis(
                project, problem_statement="Connector defect rate increased", method="five_whys",
                candidate_causes=("Torque variation",), verified_causes=("Torque variation",),
                next_actions=("Verify standard work",), analysis_evidence=(), actor="quality.engineer",
                occurred_at="2026-11-08T10:05:00+09:00", why_chain=steps[:4],
            )
        self.assertEqual(context.exception.detail.code, "five_whys_requires_five_steps")

    def test_measurement_plan_revisions_keep_analysis_evidence_identity(self) -> None:
        project = create_project(
            project_id="DMAIC-004", title="Connector yield", owner_ref="quality.engineer"
        )
        first_project, first = save_measurement_plan(
            project,
            primary_metric="First pass yield",
            data_source="Final inspection station",
            collection_method="Automated measurement",
            collection_frequency="Per shift",
            sampling_method="Random",
            sample_size=50,
            analysis_evidence=(
                {
                    "run_id": "spc-001",
                    "analysis_type": "spc.xbar_r",
                    "run_etag": "run-etag-001",
                    "input_digest": "a" * 64,
                },
            ),
            actor="quality.engineer",
            occurred_at="2026-10-30T09:00:00+09:00",
        )
        second_project, second = save_measurement_plan(
            first_project,
            primary_metric="First pass yield",
            data_source="Final inspection station",
            collection_method="Automated measurement",
            collection_frequency="Daily",
            sampling_method="Random",
            sample_size=80,
            analysis_evidence=(
                {
                    "run_id": "spc-001",
                    "analysis_type": "spc.xbar_r",
                    "run_etag": "run-etag-001",
                    "input_digest": "a" * 64,
                },
            ),
            actor="quality.engineer",
            occurred_at="2026-10-30T10:00:00+09:00",
        )

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(first.analysis_evidence[0].run_id, "spc-001")
        self.assertEqual(second_project.measurement_plan.document_id, second.document_id)
        self.assertNotIn("primary_metric", second_project.to_dict())
        self.assertEqual(DmaicMeasurementPlan.from_dict(first.to_dict()), first)

    def test_measurement_plan_snapshots_current_define_document_references(self) -> None:
        project = create_project(
            project_id="DMAIC-TRACE", title="Connector yield", owner_ref="quality.engineer"
        )
        project, charter = save_charter(
            project,
            business_case="Reduce scrap cost", problem_statement="Connector failures exceed target.",
            scope_in=("Assembly",), scope_out=("Supplier process",),
            success_metrics=("First pass yield",), team_refs=("quality.engineer",),
            budget=None, milestones=("Measure",), risk_refs=("RISK-001",),
            assumptions_constraints=("Line availability",), actor="quality.engineer",
            occurred_at="2026-11-03T09:00:00+09:00",
        )
        project, definition = save_problem_definition(
            project,
            problem_statement="Connector failures exceed target.", impact="Rework increases cost.",
            current_state="Yield is 93%.", target_state="Yield is 98%.",
            timeframe="This quarter.", location_scope="Assembly line 2.", severity="high",
            urgency="medium", objectives=("Reduce failures.",), actor="quality.engineer",
            occurred_at="2026-11-03T09:05:00+09:00",
        )
        _revised, plan = save_measurement_plan(
            project, primary_metric="First pass yield", data_source="Final inspection",
            collection_method="Automated", collection_frequency="Per shift",
            sampling_method="Random", sample_size=50, analysis_evidence=(),
            actor="quality.engineer", occurred_at="2026-11-03T09:10:00+09:00",
        )

        self.assertEqual(
            plan.source_documents,
            (project.charter, project.problem_definition),
        )
        self.assertEqual(plan.source_documents[0].digest, charter.digest)
        self.assertEqual(plan.source_documents[1].digest, definition.digest)
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

    def test_stakeholder_assessment_revisions_are_immutable_and_project_keeps_only_reference(self) -> None:
        project = create_project(
            project_id="DMAIC-004", title="Connector yield", owner_ref="quality.engineer"
        )
        first_project, first = save_stakeholder_assessment(
            project,
            stakeholders=({
                "stakeholder_id": "owner", "name": "Line owner", "role": "Approve changes",
                "department": "Production", "influence": 5, "interest": 4,
                "attitude": "supportive", "communication": "high",
                "concerns": ("Downtime",), "expectations": ("Stable yield",),
            },),
            actor="quality.engineer", occurred_at="2026-11-03T09:00:00+09:00",
        )
        second_project, second = save_stakeholder_assessment(
            first_project,
            stakeholders=({
                "stakeholder_id": "owner", "name": "Line owner", "role": "Approve changes",
                "department": "Production", "influence": 5, "interest": 5,
                "attitude": "supportive", "communication": "high",
                "concerns": ("Downtime",), "expectations": ("Stable yield", "Fast escalation"),
            },),
            actor="quality.engineer", occurred_at="2026-11-03T10:00:00+09:00",
        )

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(first.stakeholders[0].interest, 4)
        self.assertEqual(second_project.stakeholder_assessment.document_id, second.document_id)
        self.assertNotIn("stakeholders", second_project.to_dict())
        self.assertEqual(DmaicStakeholderAssessment.from_dict(first.to_dict()), first)

    def test_problem_definition_revisions_are_immutable_and_project_keeps_only_reference(self) -> None:
        project = create_project(
            project_id="DMAIC-006", title="Connector yield", owner_ref="quality.engineer"
        )
        first_project, first = save_problem_definition(
            project,
            problem_statement="Connector insertion defects exceed the target.",
            impact="Rework delays shipment and increases inspection cost.",
            current_state="First-pass yield is 93%.",
            target_state="First-pass yield is at least 98%.",
            timeframe="Improve before the next customer audit.",
            location_scope="Line 2 connector insertion station.",
            severity="high",
            urgency="medium",
            objectives=("Reduce connector insertion defects.",),
            actor="quality.engineer",
            occurred_at="2026-11-03T09:00:00+09:00",
        )
        second_project, second = save_problem_definition(
            first_project,
            problem_statement="Connector insertion defects exceed the target.",
            impact="Rework delays shipment and increases inspection cost.",
            current_state="First-pass yield is 93%.",
            target_state="First-pass yield is at least 98%.",
            timeframe="Improve before the next customer audit.",
            location_scope="Line 2 connector insertion station.",
            severity="high",
            urgency="high",
            objectives=("Reduce connector insertion defects.", "Stabilize the inspection handoff."),
            actor="quality.engineer",
            occurred_at="2026-11-03T10:00:00+09:00",
        )
        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(first.urgency, "medium")
        self.assertEqual(second_project.problem_definition.document_id, second.document_id)
        self.assertNotIn("problem_statement", second_project.to_dict())
        self.assertEqual(DmaicProblemDefinition.from_dict(first.to_dict()), first)


if __name__ == "__main__":
    unittest.main()
