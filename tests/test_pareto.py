from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.quality_tools import ParetoInputError, pareto_analysis


class ParetoAnalysisTests(unittest.TestCase):
    def test_merges_duplicates_and_marks_the_threshold_crossing_category(self) -> None:
        result = pareto_analysis(
            [("스크래치", 30), ("오염", 20), ("스크래치", 10), ("찍힘", 10)],
            threshold_percentage=80,
            subject="조립 외관 불량",
            source_sheet_id="assembly-defects",
            source_snapshot_digest="a" * 64,
        )

        rows = result.tables["pareto"]
        self.assertEqual([row["category"] for row in rows], ["스크래치", "오염", "찍힘"])
        self.assertEqual([row["value"] for row in rows], [40.0, 20.0, 10.0])
        self.assertEqual([row["vital_few"] for row in rows], [True, True, False])
        self.assertAlmostEqual(rows[1]["cumulative_percentage"], 85.71428571428571)
        self.assertEqual(result.tables["summary"]["vital_few_count"], 2)
        self.assertEqual(result.parameters["source_sheet_id"], "assembly-defects")

    def test_rejects_negative_and_zero_total_inputs(self) -> None:
        with self.assertRaises(ParetoInputError):
            pareto_analysis([("스크래치", -1)])
        with self.assertRaises(ParetoInputError):
            pareto_analysis([("스크래치", 0)])


if __name__ == "__main__":
    unittest.main()
