from __future__ import annotations

import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from statpro.api import create_app
from statpro.application.documents import InMemoryDocumentRepository


class LocalApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(InMemoryDocumentRepository()))

    def test_health_and_result_schema_are_available(self) -> None:
        health = self.client.get("/health")
        schema = self.client.get("/v1/schemas/result-bundle")
        openapi = self.client.get("/openapi.json")

        self.assertEqual(health.status_code, 200)
        self.assertTrue(health.json()["local_only"])
        self.assertEqual(schema.status_code, 200)
        self.assertEqual(schema.json()["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(openapi.status_code, 200)
        self.assertIn("/v1/analysis-runs/imr", openapi.json()["paths"])

    def test_imr_run_is_created_then_retrieved_with_same_etag(self) -> None:
        created = self.client.post(
            "/v1/analysis-runs/imr",
            json={
                "run_id": "run-001",
                "values": [1, 2, 3, 4, 5, 6],
                "rules": "western_electric",
            },
        )
        retrieved = self.client.get("/v1/analysis-runs/run-001")

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["result"]["analysis_type"], "spc.imr")
        self.assertEqual(created.json()["result"]["parameters"]["rules"], "western_electric")
        self.assertIn(
            "TREND-6",
            [
                signal["rule"]
                for signal in created.json()["result"]["plots"]["individuals"]["rule_signals"]
            ],
        )
        self.assertEqual(created.headers["etag"], retrieved.headers["etag"])
        self.assertEqual(created.json(), retrieved.json())

    def test_analysis_run_ids_are_immutable(self) -> None:
        payload = {"run_id": "run-001", "values": [1, 2, 3]}
        self.assertEqual(self.client.post("/v1/analysis-runs/imr", json=payload).status_code, 201)
        conflict = self.client.post("/v1/analysis-runs/imr", json=payload)

        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["error"]["code"], "storage_conflict")

    def test_domain_and_request_validation_are_tagged(self) -> None:
        domain_error = self.client.post(
            "/v1/analysis-runs/imr", json={"run_id": "short", "values": [1]}
        )
        request_error = self.client.post(
            "/v1/analysis-runs/imr",
            json={"run_id": "bad/id", "values": [1, 2], "unknown": True},
        )

        self.assertEqual(domain_error.status_code, 422)
        self.assertEqual(domain_error.json()["error"]["code"], "insufficient_observations")
        self.assertEqual(request_error.status_code, 422)
        self.assertEqual(request_error.json()["error"]["code"], "invalid_request")
        self.assertNotIn("input", request_error.json()["error"]["details"][0])

    def test_analysis_catalog_adapters_execute_supported_methods(self) -> None:
        requests = [
            (
                "/v1/analysis-runs/xbar-r",
                {
                    "run_id": "xbar",
                    "subgroups": [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]],
                    "rules": "nelson",
                },
                "spc.xbar_r",
            ),
            (
                "/v1/analysis-runs/capability-normal",
                {"run_id": "cap", "values": [98, 99, 100, 101, 102], "lsl": 95, "usl": 105},
                "capability.normal_individuals",
            ),
            (
                "/v1/analysis-runs/doe-full-factorial",
                {
                    "run_id": "doe",
                    "factors": [
                        {"name": "A", "low": 0, "high": 1},
                        {"name": "B", "low": 10, "high": 20},
                    ],
                    "randomize": False,
                },
                "doe.full_factorial_2level",
            ),
            (
                "/v1/analysis-runs/doe-full-factorial-analysis",
                {
                    "run_id": "doe-analysis",
                    "factors": [
                        {"name": "A", "low": 0, "high": 1},
                        {"name": "B", "low": 10, "high": 20},
                    ],
                    "responses": [10, 14, 12, 20, 12, 16, 10, 22],
                    "replicates": 2,
                    "randomize": False,
                    "interaction_order": 2,
                    "prediction_points": [{"A": 0.75, "B": 15}],
                    "optimization_goal": "maximize",
                },
                "doe.full_factorial_2level_analysis",
            ),
            (
                "/v1/analysis-runs/doe-fractional-factorial",
                {
                    "run_id": "doe-fractional",
                    "factors": [
                        {"name": name, "low": 0, "high": 1} for name in "ABCD"
                    ],
                    "generators": [{"factor": "D", "terms": ["A", "B", "C"]}],
                    "randomize": False,
                },
                "doe.fractional_factorial_2level",
            ),
            (
                "/v1/analysis-runs/doe-box-behnken",
                {
                    "run_id": "doe-box-behnken",
                    "factors": [
                        {"name": "A", "low": 0, "high": 10},
                        {"name": "B", "low": 0, "high": 20},
                        {"name": "C", "low": 0, "high": 30},
                    ],
                    "randomize": False,
                },
                "doe.box_behnken",
            ),
            (
                "/v1/analysis-runs/doe-central-composite",
                {
                    "run_id": "doe-central-composite",
                    "factors": [
                        {"name": "A", "low": 0, "high": 10},
                        {"name": "B", "low": 0, "high": 20},
                    ],
                    "center_points": 5,
                    "randomize": False,
                },
                "doe.central_composite",
            ),
            (
                "/v1/analysis-runs/doe-central-composite-analysis",
                {
                    "run_id": "doe-central-composite-analysis",
                    "factors": [
                        {"name": "A", "low": 0, "high": 10},
                        {"name": "B", "low": 0, "high": 20},
                    ],
                    "center_points": 5,
                    "randomize": False,
                    "responses": [4, 0, 8, 20, 20, 12, 4, 16, 10, 10, 10, 10, 10],
                    "response_name": "Yield",
                },
                "doe.central_composite_analysis",
            ),
            (
                "/v1/analysis-runs/doe-central-composite-surface",
                {
                    "run_id": "doe-central-composite-surface",
                    "factors": [
                        {"name": "A", "low": 0, "high": 10},
                        {"name": "B", "low": 0, "high": 20},
                    ],
                    "center_points": 5,
                    "randomize": False,
                    "responses": [8, 8, 8, 8, 8, 8, 8, 8, 10, 10, 10, 10, 10],
                    "response_name": "Yield",
                    "plot_factors": ["A", "B"],
                    "grid_size": 11,
                },
                "doe.central_composite_surface",
            ),
            (
                "/v1/analysis-runs/doe-fractional-factorial-analysis",
                {
                    "run_id": "doe-fractional-analysis",
                    "factors": [
                        {"name": name, "low": 0, "high": 1} for name in "ABCD"
                    ],
                    "generators": [{"factor": "D", "terms": ["A", "B", "C"]}],
                    "responses": [5, 9, 11, 15, 5, 9, 11, 15],
                    "response_name": "Yield",
                    "randomize": False,
                },
                "doe.fractional_factorial_2level_analysis",
            ),
            (
                "/v1/analysis-runs/doe-plackett-burman",
                {
                    "run_id": "doe-plackett-burman",
                    "factors": [
                        {"name": f"X{index}", "low": 0, "high": 10}
                        for index in range(1, 10)
                    ],
                    "runs": 12,
                    "randomize": False,
                },
                "doe.plackett_burman",
            ),
            (
                "/v1/analysis-runs/doe-plackett-burman-analysis",
                {
                    "run_id": "doe-plackett-burman-analysis",
                    "factors": [
                        {"name": "A", "low": 0, "high": 10},
                        {"name": "B", "low": 0, "high": 10},
                    ],
                    "runs": 12,
                    "randomize": False,
                    "responses": list(range(12)),
                    "response_name": "Yield",
                },
                "doe.plackett_burman_analysis",
            ),
            (
                "/v1/analysis-runs/doe-response-optimizer",
                {
                    "run_id": "doe-optimizer",
                    "factors": [
                        {"name": "A", "low": 0, "high": 1},
                        {"name": "B", "low": 0, "high": 1},
                    ],
                    "randomize": False,
                    "interaction_order": 1,
                    "objectives": [
                        {
                            "name": "Yield",
                            "responses": [0, 10, 0, 10],
                            "goal": "maximize",
                            "lower": 0,
                            "target": 10,
                        },
                        {
                            "name": "Cost",
                            "responses": [0, 0, 10, 10],
                            "goal": "minimize",
                            "target": 0,
                            "upper": 10,
                        },
                    ],
                },
                "doe.full_factorial_2level_desirability",
            ),
            (
                "/v1/analysis-runs/gage-rr-crossed",
                {
                    "run_id": "gage",
                    "records": [
                        {"part": "P1", "operator": "A", "measurement": 10},
                        {"part": "P1", "operator": "A", "measurement": 12},
                        {"part": "P1", "operator": "B", "measurement": 11},
                        {"part": "P1", "operator": "B", "measurement": 13},
                        {"part": "P2", "operator": "A", "measurement": 20},
                        {"part": "P2", "operator": "A", "measurement": 22},
                        {"part": "P2", "operator": "B", "measurement": 19},
                        {"part": "P2", "operator": "B", "measurement": 21},
                    ],
                },
                "msa.gage_rr_crossed",
            ),
        ]
        for path, payload, analysis_type in requests:
            with self.subTest(path=path):
                response = self.client.post(path, json=payload)
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["result"]["analysis_type"], analysis_type)
                if analysis_type == "spc.xbar_r":
                    self.assertEqual(response.json()["result"]["parameters"]["rules"], "nelson")
                    self.assertIn(
                        "NELSON-3",
                        [
                            signal["rule"]
                            for signal in response.json()["result"]["plots"]["xbar"]["rule_signals"]
                        ],
                    )
                if analysis_type == "doe.full_factorial_2level_analysis":
                    tables = response.json()["result"]["tables"]
                    self.assertAlmostEqual(
                        tables["predictions"][0]["predicted_response"], 16.25
                    )
                    self.assertEqual(
                        tables["optimization"][0]["actual"],
                        {"A": 1.0, "B": 20.0},
                    )
                if analysis_type == "doe.fractional_factorial_2level":
                    result = response.json()["result"]
                    self.assertEqual(result["diagnostics"]["resolution"], 4)
                    self.assertEqual(
                        result["tables"]["defining_relation"][0]["expression"],
                        "I = A*B*C*D",
                    )
                if analysis_type == "doe.central_composite":
                    result = response.json()["result"]
                    self.assertEqual(result["diagnostics"]["total_run_count"], 13)
                    self.assertTrue(result["diagnostics"]["rotatable"])
                if analysis_type == "doe.central_composite_analysis":
                    result = response.json()["result"]
                    self.assertEqual(result["diagnostics"]["coefficient_count"], 6)
                    self.assertEqual(result["diagnostics"]["response_name"], "Yield")
                if analysis_type == "doe.central_composite_surface":
                    result = response.json()["result"]
                    self.assertEqual(
                        result["diagnostics"]["stationary_classification"], "maximum"
                    )
                    self.assertEqual(result["diagnostics"]["surface_grid_point_count"], 121)
                if analysis_type == "doe.fractional_factorial_2level_analysis":
                    result = response.json()["result"]
                    self.assertEqual(result["diagnostics"]["response_name"], "Yield")
                    self.assertEqual(len(result["tables"]["coefficients"]), 4)
                if analysis_type == "doe.full_factorial_2level_desirability":
                    solution = response.json()["result"]["tables"]["solution"][0]
                    self.assertEqual(solution["actual"], {"A": 1.0, "B": 0.0})
                    self.assertAlmostEqual(solution["composite_desirability"], 1.0)

    def test_analysis_run_listing_is_bounded_and_cursor_paged(self) -> None:
        for run_id in ("run-001", "run-002", "run-003"):
            self.client.post(
                "/v1/analysis-runs/imr",
                json={"run_id": run_id, "values": [1, 2, 3]},
            )

        first = self.client.get("/v1/analysis-runs", params={"limit": 2}).json()
        second = self.client.get(
            "/v1/analysis-runs", params={"limit": 2, "after": first["next_after"]}
        ).json()

        self.assertEqual([item["run_id"] for item in first["items"]], ["run-001", "run-002"])
        self.assertEqual(first["next_after"], "run-002")
        self.assertEqual([item["run_id"] for item in second["items"]], ["run-003"])
        self.assertIsNone(second["next_after"])

    def test_fmea_study_is_created_revised_listed_and_submitted(self) -> None:
        created = self.client.post(
            "/v1/fmea-studies",
            json={
                "study_id": "PFMEA-001",
                "name": "Connector Assembly",
                "study_type": "process",
                "standard_version": "customer-standard-2026",
                "actor": "quality.engineer",
                "occurred_at": "2026-10-20T10:00:00+09:00",
            },
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["study"]["revision"], 1)

        failure = {
            "expected_storage_version": 1,
            "item_id": "FA-001",
            "structure_element": "Connector",
            "function": "Maintain contact",
            "requirement": "Resistance within specification",
            "failure_mode": "Incomplete insertion",
            "effect": "Open circuit",
            "cause": "Fixture drift",
            "prevention_control": "Setup checklist",
            "detection_control": "Continuity test",
            "ratings": {"severity": 8, "occurrence": 4, "detection": 5},
            "actor": "quality.engineer",
            "occurred_at": "2026-10-20T10:10:00+09:00",
        }
        revised = self.client.post(
            "/v1/fmea-studies/PFMEA-001/failure-analyses", json=failure
        )
        self.assertEqual(revised.status_code, 200)
        self.assertEqual(revised.json()["storage_version"], 2)
        self.assertEqual(revised.json()["study"]["items"][0]["current_ratings"]["rpn"], 160)
        self.assertEqual(revised.json()["study"]["items"][0]["action_priority_reason"], "policy_not_supplied")

        conflict = self.client.post(
            "/v1/fmea-studies/PFMEA-001/failure-analyses",
            json={**failure, "item_id": "FA-002"},
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["error"]["code"], "storage_conflict")

        listed = self.client.get("/v1/fmea-studies").json()
        self.assertEqual([item["study_id"] for item in listed["items"]], ["PFMEA-001"])

        submitted = self.client.post(
            "/v1/fmea-studies/PFMEA-001/submit-review",
            json={
                "expected_storage_version": 2,
                "actor": "quality.reviewer",
                "occurred_at": "2026-10-20T11:00:00+09:00",
            },
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json()["study"]["status"], "in_review")
        self.assertEqual(submitted.json()["study"]["revision"], 3)

    def test_fmea_action_is_completed_reassessed_and_study_approved(self) -> None:
        created = self.client.post(
            "/v1/fmea-studies",
            json={
                "study_id": "PFMEA-ACTIONS",
                "name": "Action Lifecycle",
                "study_type": "process",
                "standard_version": "customer-standard-2026",
                "actor": "quality.engineer",
                "occurred_at": "2026-10-20T10:00:00+09:00",
            },
        )
        self.assertEqual(created.status_code, 201)
        failure = self.client.post(
            "/v1/fmea-studies/PFMEA-ACTIONS/failure-analyses",
            json={
                "expected_storage_version": 1,
                "item_id": "FA-001",
                "structure_element": "Connector",
                "function": "Maintain contact",
                "requirement": "Resistance within specification",
                "failure_mode": "Incomplete insertion",
                "effect": "Open circuit",
                "cause": "Fixture drift",
                "prevention_control": "Setup checklist",
                "detection_control": "Continuity test",
                "ratings": {"severity": 8, "occurrence": 4, "detection": 5},
                "actor": "quality.engineer",
                "occurred_at": "2026-10-20T10:10:00+09:00",
            },
        )
        self.assertEqual(failure.status_code, 200)

        action = self.client.post(
            "/v1/fmea-studies/PFMEA-ACTIONS/recommended-actions",
            json={
                "expected_storage_version": 2,
                "action_id": "ACT-001",
                "item_id": "FA-001",
                "description": "Add fixture verification sensor",
                "owner": "process.engineer",
                "due_date": "2026-11-30",
                "actor": "quality.engineer",
                "occurred_at": "2026-10-20T10:20:00+09:00",
            },
        )
        self.assertEqual(action.status_code, 200)
        self.assertEqual(action.json()["study"]["actions"][0]["status"], "open")

        completed = self.client.post(
            "/v1/fmea-studies/PFMEA-ACTIONS/recommended-actions/ACT-001/complete",
            json={
                "expected_storage_version": 3,
                "result": "Sensor interlock validated on line 2",
                "evidence_refs": ["VAL-2026-014"],
                "revised_ratings": {"severity": 8, "occurrence": 2, "detection": 2},
                "actor": "process.engineer",
                "occurred_at": "2026-10-21T09:00:00+09:00",
            },
        )
        self.assertEqual(completed.status_code, 200)
        completed_study = completed.json()["study"]
        self.assertEqual(completed_study["actions"][0]["status"], "complete")
        self.assertEqual(completed_study["actions"][0]["evidence_refs"], ["VAL-2026-014"])
        self.assertEqual(completed_study["items"][0]["initial_ratings"]["rpn"], 160)
        self.assertEqual(completed_study["items"][0]["current_ratings"]["rpn"], 32)

        submitted = self.client.post(
            "/v1/fmea-studies/PFMEA-ACTIONS/submit-review",
            json={
                "expected_storage_version": 4,
                "actor": "quality.reviewer",
                "occurred_at": "2026-10-21T10:00:00+09:00",
            },
        )
        self.assertEqual(submitted.status_code, 200)
        approved = self.client.post(
            "/v1/fmea-studies/PFMEA-ACTIONS/approve",
            json={
                "expected_storage_version": 5,
                "actor": "quality.approver",
                "occurred_at": "2026-10-21T11:00:00+09:00",
            },
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["storage_version"], 6)
        self.assertEqual(approved.json()["study"]["status"], "approved")
        self.assertEqual(
            [event["event_type"] for event in approved.json()["study"]["audit_events"]],
            [
                "study_created",
                "failure_analysis_added",
                "recommended_action_added",
                "recommended_action_completed",
                "study_submitted",
                "study_approved",
            ],
        )

    def test_csv_worksheet_is_imported_revised_and_cursor_listed(self) -> None:
        content = base64.b64encode(
            b"value,accepted,note\n10.5,true,ok\n,false,check\n"
        ).decode("ascii")
        created = self.client.post(
            "/v1/worksheets/import-csv",
            json={
                "file_name": "process.csv",
                "worksheet_name": "Process Measurements",
                "content_base64": content,
            },
        )

        self.assertEqual(created.status_code, 201)
        payload = created.json()
        worksheet_id = payload["worksheet_id"]
        self.assertEqual(payload["worksheet"]["revision"], 1)
        self.assertEqual(payload["worksheet"]["columns"][0]["values"], [10.5, None])
        self.assertEqual(payload["dataset"]["source"]["location"], "process.csv")

        listed = self.client.get("/v1/worksheets", params={"limit": 1}).json()
        retrieved = self.client.get(f"/v1/worksheets/{worksheet_id}")
        self.assertEqual([item["worksheet_id"] for item in listed["items"]], [worksheet_id])
        self.assertEqual(retrieved.status_code, 200)

        revised = self.client.patch(
            f"/v1/worksheets/{worksheet_id}/cells",
            json={
                "expected_storage_version": 1,
                "row_index": 0,
                "column_name": "value",
                "value": 11.25,
            },
        )
        self.assertEqual(revised.status_code, 200)
        self.assertEqual(revised.json()["storage_version"], 2)
        self.assertEqual(revised.json()["worksheet"]["revision"], 2)
        self.assertEqual(revised.json()["worksheet"]["columns"][0]["values"][0], 11.25)
        self.assertEqual(
            revised.json()["worksheet"]["parent_digest"], payload["worksheet"]["digest"]
        )

        stale = self.client.patch(
            f"/v1/worksheets/{worksheet_id}/cells",
            json={
                "expected_storage_version": 1,
                "row_index": 0,
                "column_name": "value",
                "value": 12,
            },
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["error"]["code"], "storage_conflict")

    def test_csv_worksheet_rejects_invalid_base64(self) -> None:
        response = self.client.post(
            "/v1/worksheets/import-csv",
            json={
                "file_name": "bad.csv",
                "worksheet_name": "Bad",
                "content_base64": "not base64!",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "invalid_base64")
