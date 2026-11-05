from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.quality_dashboard import (
    QualityMetricInputError,
    create_quality_metric_snapshot,
    resolve_numeric_result_value,
)


class QualityDashboardContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = {
            "analysis_type": "spc.imr",
            "engine_version": "0.6.0",
            "input_digest": "a" * 64,
            "parameters": {"rules": "western_electric"},
            "tables": {"summary": {"center_line": 10.2}},
            "plots": {"individuals": {"values": [10.1, 10.2]}},
            "diagnostics": {"in_control_percentage": 93.1},
        }

    def test_resolves_only_finite_numeric_scalars_from_owned_sections(self) -> None:
        self.assertEqual(
            resolve_numeric_result_value(self.result, "tables.summary.center_line"),
            10.2,
        )
        self.assertEqual(
            resolve_numeric_result_value(
                self.result, "diagnostics.in_control_percentage"
            ),
            93.1,
        )

        for path in (
            "plots.individuals.values",
            "tables.summary",
            "tables.summary.missing",
        ):
            with self.subTest(path=path), self.assertRaises(QualityMetricInputError):
                resolve_numeric_result_value(self.result, path)

    def test_snapshot_preserves_run_identity_and_applies_explicit_thresholds(self) -> None:
        snapshot = create_quality_metric_snapshot(
            metric_id="line-1-center",
            name="1라인 중심선",
            unit="mm",
            run_id="imr-line-1",
            run_etag="etag-001",
            result=self.result,
            value_path="tables.summary.center_line",
            refresh_cycle="교대 종료 후",
            owner_ref="quality.line-1",
            captured_at="2026-11-05T10:00:00+09:00",
            upper_warning=10.1,
            upper_critical=10.5,
        )

        self.assertEqual(snapshot.status, "warning")
        self.assertEqual(snapshot.source.run_id, "imr-line-1")
        self.assertEqual(snapshot.source.run_etag, "etag-001")
        self.assertEqual(snapshot.source.input_digest, "a" * 64)
        self.assertEqual(len(snapshot.digest), 64)

    def test_rejects_reversed_threshold_order(self) -> None:
        with self.assertRaises(QualityMetricInputError):
            create_quality_metric_snapshot(
                metric_id="bad-threshold",
                name="잘못된 한계",
                unit="%",
                run_id="imr-line-1",
                run_etag="etag-001",
                result=self.result,
                value_path="diagnostics.in_control_percentage",
                refresh_cycle="일간",
                owner_ref="quality.line-1",
                captured_at="2026-11-05T10:00:00+09:00",
                lower_critical=95.0,
                lower_warning=90.0,
            )


if __name__ == "__main__":
    unittest.main()
