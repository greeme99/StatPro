from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.doe import (
    FactorDefinition,
    analyze_full_factorial_2level,
    full_factorial_2level,
)
from statpro.domain.errors import AnalysisInputError


class FullFactorialDesignTests(unittest.TestCase):
    def test_three_factor_standard_order_matches_nist(self) -> None:
        factors = [
            FactorDefinition("X1", 10, 20),
            FactorDefinition("X2", 1, 3),
            FactorDefinition("X3", 100, 200),
        ]
        result = full_factorial_2level(factors, randomize=False)
        coded_rows = [row["coded"] for row in result.tables["design"]]

        self.assertEqual(
            coded_rows,
            [
                {"X1": -1, "X2": -1, "X3": -1},
                {"X1": 1, "X2": -1, "X3": -1},
                {"X1": -1, "X2": 1, "X3": -1},
                {"X1": 1, "X2": 1, "X3": -1},
                {"X1": -1, "X2": -1, "X3": 1},
                {"X1": 1, "X2": -1, "X3": 1},
                {"X1": -1, "X2": 1, "X3": 1},
                {"X1": 1, "X2": 1, "X3": 1},
            ],
        )

    def test_randomization_is_reproducible_and_keeps_standard_identity(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 10, 20)]
        first = full_factorial_2level(factors, seed=42)
        second = full_factorial_2level(factors, seed=42)

        self.assertEqual(first.tables["design"], second.tables["design"])
        self.assertEqual(first.input_digest, second.input_digest)
        self.assertEqual(
            sorted(row["standard_order"] for row in first.tables["design"]), [1, 2, 3, 4]
        )

    def test_replication_and_center_points_have_expected_run_count(self) -> None:
        factors = [FactorDefinition("A", 0, 2), FactorDefinition("B", 10, 20)]
        result = full_factorial_2level(
            factors, replicates=2, center_points=2, randomize=False
        )

        self.assertEqual(result.diagnostics["total_run_count"], 10)
        centers = [row for row in result.tables["design"] if row["point_type"] == "center"]
        self.assertEqual(len(centers), 2)
        self.assertEqual(centers[0]["actual"], {"A": 1.0, "B": 15.0})

    def test_rejects_duplicate_factor_names(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("A", 2, 3)]
        with self.assertRaises(AnalysisInputError) as context:
            full_factorial_2level(factors)
        self.assertEqual(context.exception.detail.code, "duplicate_factor_name")


class FullFactorialAnalysisTests(unittest.TestCase):
    def test_replicated_two_factor_fixture_matches_hand_calculation(self) -> None:
        result = analyze_full_factorial_2level(
            [FactorDefinition("A", 0, 1), FactorDefinition("B", 10, 20)],
            [10, 14, 12, 20, 12, 16, 10, 22],
            replicates=2,
            randomize=False,
            interaction_order=2,
            response_name="Strength",
        )

        coefficients = {row["term"]: row for row in result.tables["coefficients"]}
        self.assertAlmostEqual(coefficients["Constant"]["coefficient"], 14.5)
        self.assertAlmostEqual(coefficients["A"]["effect"], 7.0)
        self.assertAlmostEqual(coefficients["B"]["effect"], 3.0)
        self.assertAlmostEqual(coefficients["A:B"]["effect"], 3.0)
        self.assertAlmostEqual(coefficients["A"]["sum_of_squares"], 98.0)
        self.assertAlmostEqual(coefficients["A"]["f_value"], 49.0)
        self.assertAlmostEqual(coefficients["A"]["p_value"], 0.002192, places=5)

        anova = {row["source"]: row for row in result.tables["anova"]}
        self.assertAlmostEqual(anova["Model"]["sum_of_squares"], 134.0)
        self.assertEqual(anova["Model"]["degrees_of_freedom"], 3)
        self.assertAlmostEqual(anova["Residual Error"]["sum_of_squares"], 8.0)
        self.assertEqual(anova["Residual Error"]["degrees_of_freedom"], 4)
        self.assertAlmostEqual(anova["Residual Error"]["mean_square"], 2.0)
        self.assertAlmostEqual(result.diagnostics["r_squared"], 134 / 142)
        self.assertAlmostEqual(result.diagnostics["adjusted_r_squared"], 1 - 2 / (142 / 7))
        self.assertEqual(result.diagnostics["pure_error_degrees_of_freedom"], 4)
        self.assertAlmostEqual(result.diagnostics["residual_standard_deviation"], 2**0.5)
        self.assertEqual(len(result.tables["residuals"]), 8)
        self.assertEqual(len(result.plots["normal_probability"]["ordered_residuals"]), 8)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_saturated_model_preserves_effects_and_marks_inference_unavailable(self) -> None:
        result = analyze_full_factorial_2level(
            [FactorDefinition("A", -1, 1), FactorDefinition("B", -1, 1)],
            [11, 15, 11, 21],
            randomize=False,
            interaction_order=2,
        )

        self.assertEqual(result.diagnostics["residual_degrees_of_freedom"], 0)
        self.assertIsNone(result.tables["anova"][0]["f_value"])
        self.assertIsNone(result.tables["coefficients"][1]["p_value"])
        self.assertTrue(any("saturated" in warning for warning in result.warnings))

    def test_rejects_response_count_and_interaction_order_mismatches(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)]
        with self.assertRaises(AnalysisInputError) as count_context:
            analyze_full_factorial_2level(factors, [1, 2, 3], randomize=False)
        self.assertEqual(count_context.exception.detail.code, "response_count_mismatch")

        with self.assertRaises(AnalysisInputError) as order_context:
            analyze_full_factorial_2level(
                factors, [1, 2, 3, 4], randomize=False, interaction_order=3
            )
        self.assertEqual(order_context.exception.detail.code, "invalid_interaction_order")

    def test_predicts_inside_design_region_and_optimizes_factorial_vertices(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 10, 20)]
        responses = [10, 14, 12, 20, 12, 16, 10, 22]
        maximize = analyze_full_factorial_2level(
            factors,
            responses,
            replicates=2,
            randomize=False,
            prediction_points=[{"A": 0.75, "B": 15}],
            optimization_goal="maximize",
        )

        prediction = maximize.tables["predictions"][0]
        self.assertEqual(prediction["coded"], {"A": 0.5, "B": 0.0})
        self.assertAlmostEqual(prediction["predicted_response"], 16.25)
        optimum = maximize.tables["optimization"][0]
        self.assertEqual(optimum["actual"], {"A": 1.0, "B": 20.0})
        self.assertAlmostEqual(optimum["predicted_response"], 21.0)
        self.assertEqual(optimum["candidate_count"], 4)

        minimize = analyze_full_factorial_2level(
            factors,
            responses,
            replicates=2,
            randomize=False,
            optimization_goal="minimize",
        )
        self.assertEqual(minimize.tables["optimization"][0]["standard_order"], 1)
        self.assertAlmostEqual(
            minimize.tables["optimization"][0]["predicted_response"], 11.0
        )

    def test_rejects_invalid_prediction_points_and_optimization_goal(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 10, 20)]
        responses = [11, 15, 11, 21]
        with self.assertRaises(AnalysisInputError) as missing_context:
            analyze_full_factorial_2level(
                factors,
                responses,
                randomize=False,
                prediction_points=[{"A": 0.5}],
            )
        self.assertEqual(missing_context.exception.detail.code, "invalid_prediction_point")

        with self.assertRaises(AnalysisInputError) as region_context:
            analyze_full_factorial_2level(
                factors,
                responses,
                randomize=False,
                prediction_points=[{"A": 2, "B": 15}],
            )
        self.assertEqual(
            region_context.exception.detail.code, "prediction_outside_design_region"
        )

        with self.assertRaises(AnalysisInputError) as goal_context:
            analyze_full_factorial_2level(
                factors,
                responses,
                randomize=False,
                optimization_goal="target",
            )
        self.assertEqual(goal_context.exception.detail.code, "invalid_optimization_goal")
