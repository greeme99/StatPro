from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.regression import best_subsets_ols, categorical_ols, interaction_ols, linear_ols, logistic_regression, negative_binomial_regression, poisson_regression, polynomial_ols, stepwise_ols, validate_ols
from statpro.analyses.descriptive import descriptive_statistics
from statpro.analyses.hypothesis import mann_whitney_u_test
from statpro.analyses.hypothesis import wilcoxon_signed_rank_test
from statpro.analyses.hypothesis import kruskal_wallis_test
from statpro.analyses.hypothesis import independent_tost_equivalence
from statpro.analyses.power import one_sample_proportion_sample_size, one_way_anova_sample_size, paired_mean_sample_size, two_sample_mean_sample_size, two_sample_proportion_sample_size
from statpro.analyses.hypothesis import one_sample_t_test
from statpro.analyses.proportion import one_sample_proportion_test
from statpro.analyses.proportion import two_sample_proportion_test
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

    def test_reports_residual_normality_and_constant_variance_diagnostics(self) -> None:
        result = linear_ols(
            [2.2, 3.8, 6.3, 7.5, 10.6, 11.1, 14.8, 15.0],
            {"temperature": list(range(1, 9))},
        )

        self.assertEqual(result.diagnostics["residual_normality_method"], "jarque_bera_asymptotic")
        self.assertEqual(result.diagnostics["residual_normality_status"], "available")
        self.assertIsNotNone(result.diagnostics["residual_normality_p_value"])
        self.assertEqual(result.diagnostics["heteroscedasticity_method"], "breusch_pagan_lm")
        self.assertEqual(result.diagnostics["heteroscedasticity_status"], "available")
        self.assertEqual(result.diagnostics["heteroscedasticity_degrees_of_freedom"], 1)
        self.assertIsNotNone(result.diagnostics["heteroscedasticity_p_value"])
        self.assertLess(result.diagnostics["heteroscedasticity_p_value"], 0.05)
        self.assertTrue(result.diagnostics["reject_constant_variance"])
        self.assertTrue(any("Breusch-Pagan" in warning for warning in result.warnings))

    def test_marks_assumption_tests_unavailable_for_zero_residual_variance(self) -> None:
        result = linear_ols([2, 4, 6, 8, 10], {"temperature": [1, 2, 3, 4, 5]})

        self.assertEqual(result.diagnostics["residual_normality_status"], "unavailable_zero_variation")
        self.assertIsNone(result.diagnostics["reject_residual_normality"])
        self.assertEqual(result.diagnostics["heteroscedasticity_status"], "unavailable_zero_variation")
        self.assertIsNone(result.diagnostics["reject_constant_variance"])


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

    def test_flags_overdispersion_with_pearson_diagnostic(self) -> None:
        result = poisson_regression([0, 20, 0, 20, 0, 20, 0, 20], {"time": list(range(8))})
        self.assertEqual(result.diagnostics["dispersion_status"], "overdispersed")
        self.assertGreater(result.diagnostics["dispersion_ratio"], 1)
        self.assertLessEqual(result.diagnostics["dispersion_p_value"], 0.05)

    def test_fits_negative_binomial_count_model_with_estimated_dispersion(self) -> None:
        result = negative_binomial_regression([0, 20, 0, 20, 0, 20, 0, 20], {"time": list(range(8))})

        self.assertEqual(result.analysis_type, "regression.negative_binomial")
        self.assertEqual(result.parameters["variance_function"], "mu + alpha * mu^2")
        self.assertEqual(len(result.tables["fitted_values"]["rows"]), 8)
        self.assertGreater(result.diagnostics["dispersion_alpha"], 0)
        self.assertIn("incidence_rate_ratio", result.tables["coefficients"]["columns"])


class DescriptiveStatisticsTests(unittest.TestCase):
    def test_summarizes_center_spread_quantiles_and_mean_interval(self) -> None:
        result = descriptive_statistics([1, 2, 3, 4, 5], variable_name="두께")
        row = result.tables["summary"]["rows"][0]
        self.assertEqual(result.analysis_type, "descriptive.univariate")
        self.assertEqual(row["variable"], "두께")
        self.assertEqual(row["n"], 5)
        self.assertEqual(row["mean"], 3)
        self.assertEqual(row["median"], 3)
        self.assertLess(row["mean_confidence_interval_lower"], 3)
        self.assertGreater(row["mean_confidence_interval_upper"], 3)


class MannWhitneyTests(unittest.TestCase):
    def test_uses_rank_sum_normal_approximation(self) -> None:
        result = mann_whitney_u_test([1, 2, 2, 3, 4], [5, 6, 7, 8, 9])
        row = result.tables["test"]["rows"][0]
        self.assertEqual(result.analysis_type, "hypothesis.mann_whitney_u")
        self.assertEqual(row["u"], 0.0)
        self.assertLess(row["p_value"], 0.05)


class WilcoxonSignedRankTests(unittest.TestCase):
    def test_excludes_zero_differences_and_reports_signed_ranks(self) -> None:
        result = wilcoxon_signed_rank_test([1, 2, 3, 4, 5], [1, 4, 5, 7, 8])
        row = result.tables["test"]["rows"][0]
        self.assertEqual(result.analysis_type, "hypothesis.wilcoxon_signed_rank")
        self.assertEqual(result.parameters["zero_difference_count"], 1)
        self.assertEqual(row["w"], 0.0)


class KruskalWallisTests(unittest.TestCase):
    def test_compares_independent_group_ranks(self) -> None:
        result = kruskal_wallis_test({"A": [1, 2, 3], "B": [5, 6, 7], "C": [9, 10, 11]})
        self.assertEqual(result.analysis_type, "hypothesis.kruskal_wallis")
        self.assertLess(result.diagnostics["p_value"], 0.05)


class IndependentTostTests(unittest.TestCase):
    def test_establishes_equivalence_when_interval_is_inside_margins(self) -> None:
        result = independent_tost_equivalence([100, 101, 99, 100], [100.1, 99.9, 100.2, 100], lower_margin=-2, upper_margin=2)
        self.assertEqual(result.analysis_type, "hypothesis.independent_tost_equivalence")
        self.assertTrue(result.diagnostics["equivalent"])


class PowerAnalysisTests(unittest.TestCase):
    def test_plans_balanced_two_sample_size(self) -> None:
        result = two_sample_mean_sample_size(difference=1, standard_deviation=1, alpha=0.05, target_power=0.8)
        self.assertEqual(result.analysis_type, "power.two_sample_mean")
        self.assertGreaterEqual(result.diagnostics["sample_size_per_group"], 16)

    def test_plans_balanced_two_proportion_size(self) -> None:
        result = two_sample_proportion_sample_size(proportion_a=0.2, proportion_b=0.05, alpha=0.05, target_power=0.8)
        self.assertEqual(result.analysis_type, "power.two_sample_proportion")
        self.assertGreater(result.diagnostics["sample_size_per_group"], 0)

    def test_plans_one_sample_proportion_size(self) -> None:
        result = one_sample_proportion_sample_size(null_proportion=0.05, expected_proportion=0.12, alpha=0.05, target_power=0.8)
        self.assertEqual(result.analysis_type, "power.one_sample_proportion")
        self.assertGreater(result.diagnostics["required_sample_size"], 0)

    def test_plans_paired_mean_size(self) -> None:
        result = paired_mean_sample_size(difference=1, difference_standard_deviation=1, alpha=0.05, target_power=0.8)
        self.assertEqual(result.analysis_type, "power.paired_mean")
        self.assertGreaterEqual(result.diagnostics["required_pairs"], 8)

    def test_plans_balanced_one_way_anova_size_against_pwr_reference(self) -> None:
        result = one_way_anova_sample_size(group_count=4, effect_size=0.25, alpha=0.05, target_power=0.8)
        self.assertEqual(result.analysis_type, "power.one_way_anova")
        self.assertEqual(result.diagnostics["sample_size_per_group"], 45)
        self.assertEqual(result.diagnostics["total_sample_size"], 180)
        self.assertGreaterEqual(result.diagnostics["achieved_power"], 0.8)

    def test_rejects_two_group_anova_plan(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            one_way_anova_sample_size(group_count=2, effect_size=0.25)
        self.assertEqual(raised.exception.detail.code, "invalid_group_count")


class OneSampleTTests(unittest.TestCase):
    def test_compares_process_mean_with_target(self) -> None:
        result = one_sample_t_test([101, 102, 103, 104, 105], target=100, variable_name="강도")
        self.assertEqual(result.analysis_type, "hypothesis.one_sample_t")
        self.assertTrue(result.diagnostics["significant"])


class OneSampleProportionTests(unittest.TestCase):
    def test_compares_defect_rate_with_target_and_reports_wilson_interval(self) -> None:
        result = one_sample_proportion_test(defects=20, opportunities=100, target=.05)
        self.assertTrue(result.diagnostics["significant"])
        self.assertGreater(result.diagnostics["wilson_upper"], result.diagnostics["wilson_lower"])


class TwoSampleProportionTests(unittest.TestCase):
    def test_compares_independent_defect_rates(self) -> None:
        result = two_sample_proportion_test(defects_a=20, opportunities_a=100, defects_b=5, opportunities_b=100)
        self.assertTrue(result.diagnostics["significant"])


if __name__ == "__main__":
    unittest.main()
