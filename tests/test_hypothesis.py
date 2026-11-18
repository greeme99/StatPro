from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.hypothesis import independent_welch_t_test
from statpro.analyses.hypothesis import paired_t_test
from statpro.domain.errors import AnalysisInputError


class IndependentWelchTTests(unittest.TestCase):
    def test_returns_welch_statistics_and_confidence_interval(self) -> None:
        result = independent_welch_t_test([1, 2, 3, 4, 5], [2, 3, 4, 5, 6], group_a_name="Before", group_b_name="After")
        row = result.tables["test"]["rows"][0]
        self.assertEqual(result.analysis_type, "hypothesis.independent_welch_t")
        self.assertAlmostEqual(row["difference"], -1.0)
        self.assertAlmostEqual(row["t_statistic"], -1.0)
        self.assertGreater(row["p_value"], 0.3)
        self.assertLess(row["p_value"], 0.4)
        self.assertLess(row["confidence_interval_lower"], -1.0)
        self.assertGreater(row["confidence_interval_upper"], -1.0)

    def test_rejects_zero_standard_error(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            independent_welch_t_test([1, 1], [2, 2])
        self.assertEqual(raised.exception.detail.code, "zero_standard_error")

    def test_returns_paired_difference_statistics(self) -> None:
        result = paired_t_test([10, 12, 11, 13], [8, 10, 9, 11])
        self.assertEqual(result.analysis_type, "hypothesis.paired_t")
        self.assertAlmostEqual(result.diagnostics["difference"], 2.0)
        self.assertEqual(result.diagnostics["degrees_of_freedom"], 3)
