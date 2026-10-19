from __future__ import annotations

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
            json={"run_id": "run-001", "values": [1, 2, 3]},
        )
        retrieved = self.client.get("/v1/analysis-runs/run-001")

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["result"]["analysis_type"], "spc.imr")
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
                {"run_id": "xbar", "subgroups": [[1, 2], [2, 3]]},
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
