from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.regression import best_subsets_ols, categorical_ols, interaction_ols, linear_ols, logistic_regression, poisson_regression, polynomial_ols, stepwise_ols, validate_ols
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

    def test_reports_vif_and_observation_prediction_intervals(self) -> None:
        result = linear_ols(
            [12, 15, 17, 21, 24, 28, 30, 35],
            {
                "temperature": [1, 2, 3, 4, 5, 6, 7, 8],
                "pressure": [3, 1, 4, 2, 5, 3, 6, 4],
            },
            response_name="Yield",
        )

        collinearity = result.tables["collinearity"]["rows"]
        fitted = result.tables["fitted_values"]["rows"]

        self.assertEqual([row["term"] for row in collinearity], ["temperature", "pressure"])
        self.assertTrue(all(row["vif"] >= 1.0 for row in collinearity))
        self.assertTrue(all(0.0 < row["tolerance"] <= 1.0 for row in collinearity))
        self.assertLess(fitted[0]["prediction_interval_lower"], fitted[0]["fitted"])
        self.assertGreater(fitted[0]["prediction_interval_upper"], fitted[0]["fitted"])
        self.assertEqual(result.diagnostics["prediction_interval_confidence"], 0.95)

    def test_reports_influence_diagnostics_for_an_outlying_observation(self) -> None:
        result = linear_ols(
            [2, 4, 6, 8, 10, 12, 14, 50],
            {"temperature": [1, 2, 3, 4, 5, 6, 7, 8]},
            response_name="Yield",
        )

        fitted = result.tables["fitted_values"]["rows"]
        outlier = fitted[-1]

        self.assertGreater(outlier["standardized_residual"], 1.0)
        self.assertGreater(outlier["studentized_residual"], 1.0)
        self.assertGreater(outlier["cooks_distance"], 1.0)
        self.assertGreater(outlier["dffits"], 1.0)
        self.assertEqual(result.diagnostics["influence_thresholds"]["cooks_distance"], 0.5)


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


class StepwiseRegressionTests(unittest.TestCase):
    def test_forward_selection_keeps_main_effects_for_a_selected_interaction(self) -> None:
        pairs = [(temperature, pressure) for temperature in [-2, -1, 0, 1, 2] for pressure in [-1, 1] for _ in range(2)]
        result = stepwise_ols(
            [2 + 3 * temperature + 10 * pressure + 5 * temperature * pressure + (0.2 if index % 2 else -0.2) for index, (temperature, pressure) in enumerate(pairs)],
            {"temperature": [temperature for temperature, _ in pairs], "pressure": [pressure for _, pressure in pairs]},
            interaction_terms=True,
            method="forward",
        )
        selected = result.parameters["selected_terms"]
        self.assertEqual(result.analysis_type, "regression.stepwise_ols")
        self.assertIn("temperature", selected)
        self.assertIn("pressure", selected)
        self.assertIn("temperature*pressure", selected)
        self.assertGreater(len(result.tables["selection_history"]["rows"]), 0)
        self.assertIn("aicc", result.diagnostics)
        self.assertIn("bic", result.diagnostics)

    def test_backward_selection_removes_non_significant_terms(self) -> None:
        result = stepwise_ols(
            [3, 5, 8, 12, 17, 23, 30, 38, 47, 57],
            {"temperature": list(range(1, 11)), "pressure": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]},
            interaction_terms=True,
            method="backward",
        )

        self.assertEqual(result.parameters["selected_terms"], ["temperature"])
        self.assertEqual([row["action"] for row in result.tables["selection_history"]["rows"]], ["remove", "remove"])


class OlsValidationTests(unittest.TestCase):
    def test_reports_deterministic_k_fold_metrics(self) -> None:
        result = validate_ols(
            [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],
            {"temperature": list(range(10))},
            method="k_fold",
            folds=5,
        )

        self.assertEqual(result.analysis_type, "regression.ols_validation")
        self.assertEqual(result.parameters["fold_count"], 5)
        self.assertEqual(len(result.tables["fold_summary"]["rows"]), 5)
        self.assertIn("rmse", result.diagnostics)

    def test_rejects_k_fold_with_insufficient_rows(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            validate_ols([2, 3, 5, 7], {"temperature": [0, 1, 2, 3]}, method="k_fold", folds=5)
        self.assertEqual(raised.exception.detail.code, "insufficient_validation_observations")

    def test_reports_holdout_metrics_for_last_rows(self) -> None:
        result = validate_ols([2, 3, 5, 7, 11, 13, 17, 19, 23, 29], {"temperature": list(range(10))}, method="holdout")
        predictions = result.tables["held_out_predictions"]["rows"]
        self.assertEqual(result.parameters["validation_method"], "holdout")
        self.assertEqual([row["observation"] for row in predictions], [9, 10])
        self.assertIsNotNone(result.diagnostics["r_squared_pred"])


class BestSubsetsRegressionTests(unittest.TestCase):
    def test_ranks_the_known_two_predictor_model_first(self) -> None:
        result = best_subsets_ols(
            [8.1, 12.9, 13.1, 17.9, 18.1, 22.9, 23.1, 27.9],
            {"temperature": [1, 2, 1, 2, 1, 2, 1, 2], "pressure": [1, 1, 2, 2, 3, 3, 4, 4]},
        )
        top = result.tables["model_comparison"]["rows"][0]
        self.assertEqual(result.analysis_type, "regression.best_subsets_ols")
        self.assertEqual(top["terms"], ["temperature", "pressure"])
        self.assertIn("press", top)
        self.assertIn("mallows_cp", top)

    def test_rejects_more_than_fifteen_candidate_predictors(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            best_subsets_ols([float(index) for index in range(20)], {f"x{index}": [float(index + row) for row in range(20)] for index in range(16)})
        self.assertEqual(raised.exception.detail.code, "too_many_subset_predictors")


class CategoricalAndPoissonRegressionTests(unittest.TestCase):
    def test_reference_codes_categorical_predictors_for_ols(self) -> None:
        result = categorical_ols([10, 11, 15, 16, 10, 11, 15, 16], {"line": ["A", "A", "B", "B", "A", "A", "B", "B"]}, reference_levels={"line": "A"})
        terms = [row["term"] for row in result.tables["coefficients"]["rows"]]
        self.assertEqual(result.analysis_type, "regression.categorical_ols")
        self.assertIn("line[B]", terms)
        self.assertEqual(result.parameters["reference_levels"], {"line": "A"})

    def test_rejects_unknown_reference_level(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            categorical_ols([10, 11, 15, 16], {"line": ["A", "A", "B", "B"]}, reference_levels={"line": "C"})
        self.assertEqual(raised.exception.detail.code, "unknown_categorical_reference")

    def test_fits_non_negative_count_response_with_poisson_log_link(self) -> None:
        result = poisson_regression([1, 2, 3, 5, 8, 13, 21, 34], {"exposure": list(range(8))})
        self.assertEqual(result.analysis_type, "regression.poisson")
        self.assertEqual(len(result.tables["fitted_values"]["rows"]), 8)
        self.assertIn("incidence_rate_ratio", result.tables["coefficients"]["columns"])


if __name__ == "__main__":
    unittest.main()
