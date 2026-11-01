from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from statpro.analyses.spc import xbar_r, xbar_s


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sixsigma_0_11_1_shewhart_constants.json"
)


class SixSigmaReferenceFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_identifies_source_and_runtime_limit(self) -> None:
        package = self.fixture["package"]

        self.assertEqual(self.fixture["fixture_kind"], "source-derived-reference")
        self.assertEqual(package["name"], "SixSigma")
        self.assertEqual(package["version"], "0.11.1")
        self.assertTrue(
            any("R was not installed" in item for item in self.fixture["limitations"])
        )

    def test_xbar_r_factors_match_sixsigma_range_constants(self) -> None:
        tolerance = self.fixture["tolerances"]["xbar_r_factor_absolute"]

        for reference in self.fixture["constants"]:
            subgroup_size = reference["n"]
            subgroup = [index / (subgroup_size - 1) for index in range(subgroup_size)]
            result = xbar_r([subgroup, subgroup])
            expected = {
                "a2": 3.0 / (reference["d2"] * math.sqrt(subgroup_size)),
                "d3": max(0.0, 1.0 - 3.0 * reference["d3"] / reference["d2"]),
                "d4": 1.0 + 3.0 * reference["d3"] / reference["d2"],
            }

            with self.subTest(subgroup_size=subgroup_size):
                for name, expected_value in expected.items():
                    self.assertAlmostEqual(
                        result.parameters[name],
                        expected_value,
                        delta=tolerance,
                    )

    def test_xbar_s_c4_matches_sixsigma_gamma_formula(self) -> None:
        tolerance = self.fixture["tolerances"]["c4_absolute"]

        for reference in self.fixture["constants"]:
            subgroup_size = reference["n"]
            subgroup = [float(index) for index in range(subgroup_size)]
            result = xbar_s([subgroup, subgroup])

            with self.subTest(subgroup_size=subgroup_size):
                self.assertAlmostEqual(
                    result.parameters["c4"],
                    reference["c4"],
                    delta=tolerance,
                )


if __name__ == "__main__":
    unittest.main()
