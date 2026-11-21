from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.application.audit_ledger import ApiAuditLedger, AuditLedgerError
from statpro.application.documents import InMemoryDocumentRepository


class ApiAuditLedgerTests(unittest.TestCase):
    def test_append_creates_a_verifiable_hash_chain_without_request_content(self) -> None:
        repository = InMemoryDocumentRepository()
        ledger = ApiAuditLedger(repository)

        first = ledger.append(
            actor="M15082", permission="quality.edit", method="POST",
            path="/v1/worksheets", request_digest="a" * 64,
            response_status=201, response_etag='"worksheet-digest"',
        )
        second = ledger.append(
            actor="M15082", permission="quality.export", method="GET",
            path="/v1/analysis-runs/run-001/export", request_digest="b" * 64,
            response_status=200, response_etag=None,
        )

        self.assertEqual(second["previous_event_hash"], first["event_hash"])
        self.assertNotIn("request_body", first)
        self.assertEqual(ledger.verify()["event_count"], 2)
        exported = ledger.export()
        self.assertTrue(exported["verification"]["valid"])
        self.assertEqual(len(exported["events"]), 2)

    def test_verify_rejects_a_tampered_event(self) -> None:
        repository = InMemoryDocumentRepository()
        ledger = ApiAuditLedger(repository)
        event = ledger.append(
            actor="M15082", permission="quality.edit", method="POST",
            path="/v1/worksheets", request_digest="a" * 64,
            response_status=201, response_etag=None,
        )
        stored = next(
            candidate
            for candidate in repository.list_documents("api-audit-events", after=None, limit=10)
            if candidate.key != "api-audit-head"
        )
        repository.save(
            "api-audit-events", stored.key,
            {**event, "path": "/v1/altered"},
            expected_version=stored.storage_version,
        )

        with self.assertRaises(AuditLedgerError):
            ledger.verify()


if __name__ == "__main__":
    unittest.main()
