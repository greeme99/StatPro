from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.capability import nonnormal_process_capability, normal_process_capability
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

    def test_nonnormal_indices_use_empirical_tail_quantiles(self) -> None:
        result = nonnormal_process_capability(
            [1, 1, 2, 2, 3, 3, 4, 5, 8, 13], lsl=0, usl=15, target=3
        )
        summary = result.tables["summary"]
        indices = result.tables["indices"]

        self.assertEqual(result.analysis_type, "capability.nonnormal_empirical")
        self.assertAlmostEqual(summary["median"], 3.0)
        self.assertLess(summary["lower_quantile"], summary["median"])
        self.assertGreater(summary["upper_quantile"], summary["median"])
        self.assertAlmostEqual(indices["cnpl"], 3.0 / (3.0 - summary["lower_quantile"]))
        self.assertAlmostEqual(indices["cnpu"], 12.0 / (summary["upper_quantile"] - 3.0))
        self.assertEqual(indices["cnpk"], min(indices["cnpl"], indices["cnpu"]))
        self.assertIsNotNone(indices["cnpm"])
        self.assertIn("NIST/SEMATECH 6.1.6", result.provenance[1].title)

    def test_nonnormal_one_sided_spec_omits_width_index(self) -> None:
        result = nonnormal_process_capability([1, 2, 3, 4, 5, 7, 11], usl=14)

        self.assertIsNone(result.tables["indices"]["cnp"])
        self.assertIsNone(result.tables["indices"]["cnpl"])
        self.assertIsNotNone(result.tables["indices"]["cnpu"])

    def test_nonnormal_rejects_zero_required_tail_spread(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            nonnormal_process_capability([1, 1, 1, 1, 2], lsl=0)
        self.assertEqual(context.exception.detail.code, "zero_tail_spread")
