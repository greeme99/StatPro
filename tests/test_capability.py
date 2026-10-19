from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.capability import normal_process_capability
from statpro.domain.errors import AnalysisInputError


class NormalCapabilityTests(unittest.TestCase):
    def test_two_sided_indices_keep_within_and_overall_sigma_distinct(self) -> None:
        result = normal_process_capability([98, 99, 100, 101, 102], lsl=95, usl=105, target=100)
        summary = result.tables["summary"]
        indices = result.tables["indices"]

        self.assertAlmostEqual(summary["mean"], 100.0)
        self.assertAlmostEqual(summary["within_sigma"], 1.0 / 1.128)
        self.assertAlmostEqual(indices["cp"], 1.88)
        self.assertAlmostEqual(indices["cpk"], 1.88)
        self.assertAlmostEqual(indices["pp"], 10.0 / (6.0 * (2.5**0.5)))
        self.assertAlmostEqual(indices["ppk"], indices["pp"])
        self.assertAlmostEqual(indices["cpm"], indices["pp"])

    def test_one_sided_spec_omits_width_indices(self) -> None:
        result = normal_process_capability([98, 99, 100, 101, 102], lsl=95)
        indices = result.tables["indices"]

        self.assertIsNone(indices["cp"])
        self.assertIsNone(indices["pp"])
        self.assertIsNotNone(indices["cpl"])
        self.assertEqual(indices["cpk"], indices["cpl"])

    def test_rejects_reversed_specification_limits(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            normal_process_capability([1, 2, 3], lsl=4, usl=2)
        self.assertEqual(context.exception.detail.code, "invalid_specification_limits")

    def test_rejects_zero_variation(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            normal_process_capability([1, 1, 1], lsl=0, usl=2)
        self.assertEqual(context.exception.detail.code, "zero_variation")
