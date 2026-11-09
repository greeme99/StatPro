from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.regression import linear_ols
from statpro.domain.errors import AnalysisInputError


class LinearOlsTests(unittest.TestCase):
    def test_returns_coefficients_anova_and_fitted_residuals(self) -> None:
        result = linear_ols([2, 3, 5, 7, 11, 13], {"temperature": [0, 1, 2, 3, 4, 5]}, response_name="Yield")
        coefficients = result.tables["coefficients"]["rows"]
        self.assertEqual(result.analysis_type, "regression.linear_ols")
        self.assertAlmostEqual(coefficients[0]["coefficient"], 1.0476190476190474)
        self.assertAlmostEqual(coefficients[1]["coefficient"], 2.3142857142857145)
        self.assertEqual(len(result.tables["fitted_values"]["rows"]), 6)
        self.assertGreater(result.diagnostics["r_squared"], 0.9)
        self.assertIsNotNone(result.diagnostics["model_p_value"])

    def test_rejects_collinear_predictors(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            linear_ols([1, 2, 3, 4], {"x1": [1, 2, 3, 4], "x2": [2, 4, 6, 8]})
        self.assertEqual(raised.exception.detail.code, "singular_design_matrix")

    def test_rejects_response_with_no_residual_degrees_of_freedom(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            linear_ols([1, 2], {"x": [1, 2]})
        self.assertEqual(raised.exception.detail.code, "insufficient_observations")


if __name__ == "__main__":
    unittest.main()
