from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.spc import individuals_moving_range, xbar_r
from statpro.domain.errors import AnalysisInputError


class IndividualsMovingRangeTests(unittest.TestCase):
    def test_matches_nist_flow_rate_example(self) -> None:
        result = individuals_moving_range(
            [49.6, 47.6, 49.9, 51.3, 47.8, 51.2, 52.6, 52.4, 53.6, 52.1]
        )
        limits = result.tables["limits"]["individuals"]

        self.assertAlmostEqual(limits["center"], 50.81, places=12)
        self.assertAlmostEqual(result.tables["limits"]["moving_range"]["center"], 1.8777777778, places=9)
        # NIST publishes limits to four decimal places after displaying MR-bar rounded
        # to 1.8778. StatPro retains the unrounded intermediate value.
        self.assertAlmostEqual(limits["ucl"], 55.8041, places=4)
        self.assertAlmostEqual(limits["lcl"], 45.8159, places=4)
        self.assertEqual(result.diagnostics["individual_signal_indices"], [])

    def test_rejects_non_finite_values(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            individuals_moving_range([1.0, math.nan])
        self.assertEqual(context.exception.detail.code, "non_finite_value")

    def test_digest_is_deterministic(self) -> None:
        first = individuals_moving_range([1, 2, 3])
        second = individuals_moving_range([1.0, 2.0, 3.0])
        self.assertEqual(first.input_digest, second.input_digest)


class XbarRTests(unittest.TestCase):
    def test_hand_calculated_two_item_subgroups(self) -> None:
        result = xbar_r([[1, 2], [3, 4]])
        xbar_limits = result.tables["limits"]["xbar"]
        range_limits = result.tables["limits"]["range"]

        self.assertAlmostEqual(xbar_limits["center"], 2.5)
        self.assertAlmostEqual(xbar_limits["lcl"], 0.62)
        self.assertAlmostEqual(xbar_limits["ucl"], 4.38)
        self.assertAlmostEqual(range_limits["center"], 1.0)
        self.assertAlmostEqual(range_limits["lcl"], 0.0)
        self.assertAlmostEqual(range_limits["ucl"], 3.267)

    def test_rejects_unequal_subgroups(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            xbar_r([[1, 2], [3, 4, 5]])
        self.assertEqual(context.exception.detail.code, "unequal_subgroup_size")

    def test_warns_when_within_subgroup_variation_is_zero(self) -> None:
        result = xbar_r([[1, 1], [2, 2]])
        self.assertEqual(len(result.warnings), 1)


if __name__ == "__main__":
    unittest.main()
