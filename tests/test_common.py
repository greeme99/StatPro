from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.common import chi_square_quantile
from statpro.domain.errors import AnalysisInputError


class ChiSquareQuantileTests(unittest.TestCase):
    def test_matches_standard_four_degree_of_freedom_reference_quantiles(self) -> None:
        self.assertAlmostEqual(chi_square_quantile(0.025, 4), 0.484418557, places=7)
        self.assertAlmostEqual(chi_square_quantile(0.975, 4), 11.14328678, places=7)

    def test_rejects_non_probability_and_nonpositive_degrees_of_freedom(self) -> None:
        for probability, degrees_of_freedom in ((0.0, 4), (1.0, 4), (0.5, 0)):
            with self.assertRaises(AnalysisInputError) as context:
                chi_square_quantile(probability, degrees_of_freedom)
            self.assertEqual(context.exception.detail.code, "invalid_distribution_parameter")


if __name__ == "__main__":
    unittest.main()
