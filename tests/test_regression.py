from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.regression import interaction_ols, linear_ols, logistic_regression, polynomial_ols
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


class LogisticRegressionTests(unittest.TestCase):
    def test_returns_odds_ratio_intervals_and_probabilities(self) -> None:
        result = logistic_regression([0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0], {"temperature": list(range(12))})
        coefficient = result.tables["coefficients"]["rows"][1]
        self.assertEqual(result.analysis_type, "regression.logistic")
        self.assertGreater(coefficient["odds_ratio"], 0)
        self.assertLess(coefficient["odds_ratio_ci_lower"], coefficient["odds_ratio_ci_upper"])
        self.assertEqual(len(result.tables["fitted_values"]["rows"]), 12)
        self.assertLess(result.diagnostics["log_likelihood"], 0)
        self.assertEqual(result.diagnostics["classification_threshold"], 0.5)
        self.assertGreaterEqual(result.diagnostics["classification_accuracy"], 0)
        self.assertLessEqual(result.diagnostics["classification_accuracy"], 1)


class PolynomialRegressionTests(unittest.TestCase):
    def test_expands_predictors_to_the_requested_degree(self) -> None:
        result = polynomial_ols(
            [2.2, 4.8, 10.2, 17.8, 27.8, 39.8],
            {"temperature": [1, 2, 3, 4, 5, 6]},
            response_name="Yield",
            degree=2,
        )
        terms = [row["term"] for row in result.tables["coefficients"]["rows"]]
        self.assertEqual(result.analysis_type, "regression.polynomial_ols")
        self.assertEqual(terms, ["Intercept", "temperature", "temperature^2"])
        self.assertEqual(result.parameters["degree"], 2)
        self.assertEqual(result.parameters["source_predictor_names"], ["temperature"])
        self.assertGreater(result.diagnostics["r_squared"], 0.99)


class InteractionRegressionTests(unittest.TestCase):
    def test_adds_requested_two_factor_interaction_terms(self) -> None:
        result = interaction_ols(
            [3, 5, 8, 12, 17, 23, 30, 38],
            {
                "temperature": [1, 2, 3, 4, 5, 6, 7, 8],
                "pressure": [2, 1, 2, 1, 2, 1, 2, 1],
            },
            response_name="Yield",
        )
        terms = [row["term"] for row in result.tables["coefficients"]["rows"]]
        self.assertEqual(result.analysis_type, "regression.interaction_ols")
        self.assertIn("temperature*pressure", terms)
        self.assertEqual(result.parameters["interaction_order"], 2)


if __name__ == "__main__":
    unittest.main()
