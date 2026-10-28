from __future__ import annotations

import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.doe import FactorDefinition, full_factorial_2level
from statpro.application.documents import InMemoryDocumentRepository
from statpro.application.reports import (
    REPORT_TYPE,
    build_doe_report,
    export_doe_report_zip,
    render_doe_report_html,
)


class DoeReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryDocumentRepository()
        result = full_factorial_2level(
            [FactorDefinition("A", 0, 1), FactorDefinition("B", 10, 20)],
            randomize=False,
        )
        self.stored = self.repository.save(
            "analysis-runs",
            "doe-report-001",
            {
                "kind": "analysis_run",
                "run_id": "doe-report-001",
                "result": result.to_dict(),
            },
            expected_version=0,
        )

    def test_report_preserves_run_identity_and_result_sections(self) -> None:
        report = build_doe_report(self.stored)

        self.assertEqual(report["report_type"], REPORT_TYPE)
        self.assertEqual(report["run"]["run_id"], "doe-report-001")
        self.assertEqual(report["run"]["etag"], self.stored.etag)
        self.assertEqual(report["analysis"]["input_digest"], self.stored.document["result"]["input_digest"])
        self.assertEqual(report["tables"][0]["row_count"], 4)
        self.assertEqual(build_doe_report(self.stored), report)

    def test_html_and_zip_export_are_complete_and_deterministic(self) -> None:
        report = build_doe_report(self.stored)
        html = render_doe_report_html(report)
        first = export_doe_report_zip(report)
        second = export_doe_report_zip(report)

        self.assertIn(b"StatPro DOE Analysis Report", html)
        self.assertIn(b"Plot data", html)
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(
                archive.namelist(),
                ["report.html", "report.json", "tables/01-design.csv"],
            )
            exported = json.loads(archive.read("report.json"))
            csv_text = archive.read("tables/01-design.csv").decode("utf-8-sig")
        self.assertEqual(exported["report_digest"], report["report_digest"])
        self.assertIn("run_order,standard_order", csv_text)


if __name__ == "__main__":
    unittest.main()
