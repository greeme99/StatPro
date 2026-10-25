from __future__ import annotations

import json
import sys
import unittest
from math import sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    ResponseObjective,
    analyze_automatic_fractional_factorial_2level,
    analyze_box_behnken,
    analyze_central_composite,
    analyze_fractional_factorial_2level,
    analyze_full_factorial_2level,
    analyze_plackett_burman,
    automatic_fractional_factorial_2level,
    box_behnken_design,
    central_composite_design,
    composite_desirability,
    explore_central_composite_surface,
    fractional_factorial_2level,
    full_factorial_2level,
    individual_desirability,
    optimize_full_factorial_desirability,
    plackett_burman_design,
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


class FractionalFactorialDesignTests(unittest.TestCase):
    def test_block_generators_assign_balanced_blocks_and_aliases(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        result = fractional_factorial_2level(
            factors,
            [GeneratorDefinition("E", ["A", "B", "C", "D"])],
            block_generators=[["A", "B"], ["A", "C"]],
            randomize=False,
        )

        self.assertEqual(result.diagnostics["block_count"], 4)
        self.assertEqual(result.diagnostics["runs_per_block"], 4)
        self.assertEqual(result.diagnostics["blocked_resolution"], 3)
        self.assertEqual(
            [row["block"] for row in result.tables["design"]],
            [1] * 4 + [2] * 4 + [3] * 4 + [4] * 4,
        )
        self.assertEqual(
            result.tables["block_aliases"],
            [
                {
                    "contrast": "Blk1",
                    "generator_terms": "A*B",
                    "treatment_alias_set": ["A*B", "C*D*E"],
                },
                {
                    "contrast": "Blk2",
                    "generator_terms": "A*C",
                    "treatment_alias_set": ["A*C", "B*D*E"],
                },
                {
                    "contrast": "Blk1*Blk2",
                    "generator_terms": "B*C",
                    "treatment_alias_set": ["B*C", "A*D*E"],
                },
            ],
        )

    def test_block_generators_reject_dependency_and_main_effect_confounding(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        generator = [GeneratorDefinition("E", ["A", "B", "C", "D"])]
        with self.assertRaises(AnalysisInputError) as dependent:
            fractional_factorial_2level(
                factors,
                generator,
                block_generators=[["A", "B"], ["C", "D", "E"]],
            )
        self.assertEqual(dependent.exception.detail.code, "dependent_block_generators")

        with self.assertRaises(AnalysisInputError) as main_effect:
            fractional_factorial_2level(
                factors,
                generator,
                block_generators=[["A", "B", "C", "D"]],
            )
        self.assertEqual(main_effect.exception.detail.code, "block_confounds_main_effect")

    def test_blocked_analysis_fits_block_contrasts_as_nuisance_terms(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        generator = [GeneratorDefinition("E", ["A", "B", "C", "D"])]
        design = fractional_factorial_2level(
            factors,
            generator,
            block_generators=[["A", "B"], ["A", "C"]],
            randomize=False,
        )
        responses = [
            10 + 2 * row["coded"]["A"] + 5 * row["block_contrasts"]["Blk1"]
            for row in design.tables["design"]
        ]
        result = analyze_fractional_factorial_2level(
            factors,
            generator,
            responses,
            block_generators=[["A", "B"], ["A", "C"]],
            randomize=False,
        )

        coefficients = {
            row["term"]: row["coefficient"] for row in result.tables["coefficients"]
        }
        blocks = {
            row["contrast"]: row["coefficient"]
            for row in result.tables["block_effects"]
        }
        self.assertAlmostEqual(coefficients["A"], 2.0)
        self.assertAlmostEqual(blocks["Blk1"], 5.0)
        self.assertAlmostEqual(blocks["Blk2"], 0.0)
        self.assertEqual(result.diagnostics["block_degrees_of_freedom"], 3)
        self.assertTrue(all(abs(row["residual"]) < 1e-12 for row in result.tables["residuals"]))

    def test_automatic_selection_matches_minimum_aberration_quarter_fraction(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        result = automatic_fractional_factorial_2level(
            factors,
            runs=8,
            minimum_resolution=3,
            randomize=False,
        )

        self.assertEqual(
            result.tables["generators"],
            [
                {"factor": "D", "terms": ["A", "B"], "expression": "D=A*B"},
                {"factor": "E", "terms": ["A", "C"], "expression": "E=A*C"},
            ],
        )
        self.assertEqual(result.diagnostics["resolution"], 3)
        self.assertEqual(
            result.diagnostics["word_length_pattern"], {"3": 2, "4": 1, "5": 0}
        )
        self.assertEqual(result.diagnostics["candidate_sets_examined"], 6)
        self.assertTrue(result.diagnostics["search_space_complete"])
        self.assertEqual(
            result.parameters["generator_selection"]["selection_objective"],
            "minimum_aberration_at_requested_runs",
        )

    def test_automatic_selection_chooses_smallest_runs_meeting_resolution(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDEF"]
        first = automatic_fractional_factorial_2level(
            factors,
            minimum_resolution=4,
            randomize=False,
        )
        second = automatic_fractional_factorial_2level(
            factors,
            minimum_resolution=4,
            randomize=False,
        )

        self.assertEqual(first.diagnostics["selected_base_run_count"], 16)
        self.assertEqual(first.diagnostics["resolution"], 4)
        self.assertEqual(first.diagnostics["word_length_pattern"]["3"], 0)
        self.assertEqual(first.tables["generators"], second.tables["generators"])
        self.assertEqual(first.input_digest, second.input_digest)

    def test_automatic_selection_rejects_unavailable_resolution_at_fixed_runs(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDEF"]
        with self.assertRaises(AnalysisInputError) as context:
            automatic_fractional_factorial_2level(
                factors,
                runs=8,
                minimum_resolution=4,
            )
        self.assertEqual(context.exception.detail.code, "automatic_generator_unavailable")

    def test_automatic_analysis_retains_selection_and_alias_evidence(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        design = automatic_fractional_factorial_2level(
            factors,
            runs=8,
            randomize=False,
        )
        responses = [
            10 + 2 * row["coded"]["A"] + 3 * row["coded"]["B"]
            for row in design.tables["design"]
        ]
        result = analyze_automatic_fractional_factorial_2level(
            factors,
            responses,
            runs=8,
            randomize=False,
        )

        self.assertEqual(result.diagnostics["generator_selection_mode"], "automatic")
        self.assertEqual(result.diagnostics["selected_base_run_count"], 8)
        self.assertEqual(result.parameters["generator_selection"]["mode"], "automatic")
        self.assertEqual(len(result.tables["main_effect_aliases"]), 5)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_half_fraction_standard_order_relation_resolution_and_aliases(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCD"]
        result = fractional_factorial_2level(
            factors,
            [GeneratorDefinition("D", ["A", "B", "C"])],
            randomize=False,
        )

        coded_rows = [row["coded"] for row in result.tables["design"]]
        self.assertEqual(len(coded_rows), 8)
        self.assertEqual(coded_rows[0], {"A": -1, "B": -1, "C": -1, "D": -1})
        self.assertEqual(coded_rows[-1], {"A": 1, "B": 1, "C": 1, "D": 1})
        self.assertTrue(all(row["D"] == row["A"] * row["B"] * row["C"] for row in coded_rows))
        self.assertEqual(result.tables["defining_relation"][0]["expression"], "I = A*B*C*D")
        self.assertEqual(result.diagnostics["design_notation"], "2^(4-1)")
        self.assertEqual(result.diagnostics["resolution"], 4)
        main_aliases = {
            row["effect"]: row["alias_set"] for row in result.tables["main_effect_aliases"]
        }
        interaction_aliases = {
            row["effect"]: row["alias_set"]
            for row in result.tables["two_factor_aliases"]
        }
        self.assertEqual(main_aliases["A"], ["A", "B*C*D"])
        self.assertEqual(interaction_aliases["A*B"], ["A*B", "C*D"])
        json.dumps(result.to_dict(), allow_nan=False)

    def test_multiple_generators_form_complete_defining_relation(self) -> None:
        result = fractional_factorial_2level(
            [FactorDefinition(name, -1, 1) for name in "ABCDE"],
            [
                GeneratorDefinition("D", ["A", "B"]),
                GeneratorDefinition("E", ["A", "C"]),
            ],
            randomize=False,
        )

        self.assertEqual(
            set(result.tables["defining_relation"][0]["words"]),
            {"A*B*D", "A*C*E", "B*C*D*E"},
        )
        self.assertEqual(result.diagnostics["resolution"], 3)
        self.assertEqual(result.diagnostics["fraction"], "1/4")

    def test_randomization_is_reproducible(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCD"]
        generators = [GeneratorDefinition("D", ["A", "B", "C"])]
        first = fractional_factorial_2level(factors, generators, seed=17)
        second = fractional_factorial_2level(factors, generators, seed=17)

        self.assertEqual(first.tables["design"], second.tables["design"])
        self.assertEqual(first.input_digest, second.input_digest)

    def test_resolution_three_mirror_foldover_reverses_every_sign(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        result = fractional_factorial_2level(
            factors,
            [
                GeneratorDefinition("D", ["A", "B"]),
                GeneratorDefinition("E", ["A", "C"]),
            ],
            foldover=True,
            randomize=False,
        )

        rows = result.tables["design"]
        self.assertEqual(len(rows), 16)
        for original, folded in zip(rows[:8], rows[8:], strict=True):
            self.assertEqual(original["fraction_phase"], "original")
            self.assertEqual(folded["fraction_phase"], "foldover")
            self.assertEqual(
                folded["coded"],
                {name: -value for name, value in original["coded"].items()},
            )
        self.assertEqual(result.diagnostics["augmented_resolution"], 4)
        self.assertTrue(
            result.diagnostics["main_effects_clear_of_two_factor_interactions"]
        )
        self.assertEqual(
            result.tables["defining_relation"][0]["expression"],
            "I = B*C*D*E",
        )

    def test_mirror_foldover_rejects_non_resolution_three_design(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            fractional_factorial_2level(
                [FactorDefinition(name, 0, 1) for name in "ABCD"],
                [GeneratorDefinition("D", ["A", "B", "C"])],
                foldover=True,
            )
        self.assertEqual(
            context.exception.detail.code,
            "mirror_foldover_requires_resolution_iii",
        )

    def test_rejects_generated_factor_dependencies(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        with self.assertRaises(AnalysisInputError) as context:
            fractional_factorial_2level(
                factors,
                [
                    GeneratorDefinition("D", ["A", "B"]),
                    GeneratorDefinition("E", ["A", "D"]),
                ],
            )
        self.assertEqual(context.exception.detail.code, "generator_requires_base_factors")

        with self.assertRaises(AnalysisInputError) as terms_context:
            fractional_factorial_2level(
                factors,
                [GeneratorDefinition("D", "ABC")],
            )
        self.assertEqual(terms_context.exception.detail.code, "invalid_generator_terms")

        with self.assertRaises(AnalysisInputError) as resolution_context:
            fractional_factorial_2level(
                factors,
                [
                    GeneratorDefinition("D", ["A", "B"]),
                    GeneratorDefinition("E", ["B", "A"]),
                ],
            )
        self.assertEqual(resolution_context.exception.detail.code, "resolution_too_low")


class FractionalFactorialAnalysisTests(unittest.TestCase):
    def test_main_effect_analysis_preserves_alias_interpretation(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCD"]
        design = fractional_factorial_2level(
            factors,
            [GeneratorDefinition("D", ["A", "B", "C"])],
            randomize=False,
        )
        responses = [
            10 + 2 * row["coded"]["A"] + 3 * row["coded"]["B"]
            for row in design.tables["design"]
        ]

        result = analyze_fractional_factorial_2level(
            factors,
            [GeneratorDefinition("D", ["A", "B", "C"])],
            responses,
            randomize=False,
        )

        effects = {row["term"]: row for row in result.tables["coefficients"]}
        self.assertAlmostEqual(effects["A"]["effect"], 4.0)
        self.assertAlmostEqual(effects["B"]["effect"], 6.0)
        self.assertEqual(effects["A"]["alias_set"], ["A", "B*C*D"])
        self.assertTrue(effects["A"]["clear_of_two_factor_interactions"])
        self.assertEqual(result.diagnostics["model_scope"], "main_effect_representatives")
        json.dumps(result.to_dict(), allow_nan=False)

    def test_foldover_clears_main_effect_from_two_factor_interaction(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCDE"]
        generators = [
            GeneratorDefinition("D", ["A", "B"]),
            GeneratorDefinition("E", ["A", "C"]),
        ]
        design = fractional_factorial_2level(
            factors, generators, foldover=True, randomize=False
        )
        responses = [
            10
            + 2 * row["coded"]["A"]
            + 3 * row["coded"]["B"]
            + 4 * row["coded"]["A"] * row["coded"]["B"]
            for row in design.tables["design"]
        ]

        result = analyze_fractional_factorial_2level(
            factors,
            generators,
            responses,
            response_name="Yield",
            foldover=True,
            randomize=False,
        )

        effects = {row["term"]: row for row in result.tables["coefficients"]}
        self.assertAlmostEqual(effects["A"]["effect"], 4.0)
        self.assertAlmostEqual(effects["B"]["effect"], 6.0)
        self.assertAlmostEqual(effects["D"]["effect"], 0.0)
        self.assertEqual(effects["D"]["alias_set"], ["D", "B*C*E"])
        self.assertTrue(effects["D"]["clear_of_two_factor_interactions"])
        self.assertEqual(result.diagnostics["augmented_resolution"], 4)

    def test_rejects_response_count_mismatch(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            analyze_fractional_factorial_2level(
                [FactorDefinition(name, 0, 1) for name in "ABCD"],
                [GeneratorDefinition("D", ["A", "B", "C"])],
                [1, 2, 3],
                randomize=False,
            )
        self.assertEqual(context.exception.detail.code, "response_count_mismatch")


class BoxBehnkenDesignTests(unittest.TestCase):
    def test_three_factor_standard_order_matches_nist_table(self) -> None:
        factors = [FactorDefinition(name, 10, 20) for name in "ABC"]
        result = box_behnken_design(factors, randomize=False)

        coded = [tuple(row["coded"][name] for name in "ABC") for row in result.tables["design"]]
        self.assertEqual(
            coded,
            [
                (-1.0, -1.0, 0.0),
                (1.0, -1.0, 0.0),
                (-1.0, 1.0, 0.0),
                (1.0, 1.0, 0.0),
                (-1.0, 0.0, -1.0),
                (1.0, 0.0, -1.0),
                (-1.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (0.0, -1.0, -1.0),
                (0.0, 1.0, -1.0),
                (0.0, -1.0, 1.0),
                (0.0, 1.0, 1.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
            ],
        )
        self.assertEqual(result.diagnostics["edge_block_count"], 3)
        self.assertFalse(result.diagnostics["corner_points_included"])
        self.assertTrue(result.diagnostics["quadratic_model_estimable"])

    def test_five_factor_defaults_to_six_centers_and_46_runs(self) -> None:
        result = box_behnken_design(
            [FactorDefinition(name, 0, 10) for name in "ABCDE"],
            randomize=False,
        )

        rows = result.tables["design"]
        edge_rows = [row for row in rows if row["point_type"] == "edge_midpoint"]
        self.assertEqual(len(rows), 46)
        self.assertEqual(len(edge_rows), 40)
        self.assertTrue(
            all(sum(value != 0 for value in row["coded"].values()) == 2 for row in edge_rows)
        )
        self.assertEqual(result.diagnostics["center_point_count"], 6)

    def test_randomization_is_reproducible_and_six_factors_are_rejected(self) -> None:
        factors = [FactorDefinition(name, 0, 1) for name in "ABCD"]
        first = box_behnken_design(factors, seed=19)
        second = box_behnken_design(factors, seed=19)
        self.assertEqual(first.tables["design"], second.tables["design"])
        self.assertEqual(first.input_digest, second.input_digest)

        with self.assertRaises(AnalysisInputError) as context:
            box_behnken_design([FactorDefinition(name, 0, 1) for name in "ABCDEF"])
        self.assertEqual(context.exception.detail.code, "too_many_factors")

        with self.assertRaises(AnalysisInputError) as context:
            box_behnken_design(factors, replicates=5_000)
        self.assertEqual(context.exception.detail.code, "design_too_large")


class BoxBehnkenAnalysisTests(unittest.TestCase):
    def test_complete_quadratic_model_recovers_hand_fixture(self) -> None:
        factors = [FactorDefinition(name, 0, 10) for name in "ABC"]
        design = box_behnken_design(factors, randomize=False)
        responses = []
        for row in design.tables["design"]:
            a, b, c = (row["coded"][name] for name in "ABC")
            responses.append(
                10 + 2 * a - 3 * b + 4 * c + 5 * a * b - 2 * a * c
                + 3 * b * c + 6 * a * a - 4 * b * b + 2 * c * c
            )

        result = analyze_box_behnken(
            factors,
            responses,
            response_name="Yield",
            randomize=False,
        )

        coefficients = {
            row["term"]: row["coefficient"] for row in result.tables["coefficients"]
        }
        expected = {
            "Constant": 10.0,
            "A": 2.0,
            "B": -3.0,
            "C": 4.0,
            "A*B": 5.0,
            "A*C": -2.0,
            "B*C": 3.0,
            "A^2": 6.0,
            "B^2": -4.0,
            "C^2": 2.0,
        }
        for term, value in expected.items():
            self.assertAlmostEqual(coefficients[term], value)
        self.assertEqual(result.analysis_type, "doe.box_behnken_analysis")
        self.assertAlmostEqual(result.diagnostics["r_squared"], 1.0)
        self.assertEqual(result.diagnostics["pure_error_degrees_of_freedom"], 2)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_rejects_response_count_mismatch(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            analyze_box_behnken(
                [FactorDefinition(name, 0, 1) for name in "ABC"],
                [1, 2, 3],
                randomize=False,
            )
        self.assertEqual(context.exception.detail.code, "response_count_mismatch")


class CentralCompositeDesignTests(unittest.TestCase):
    def test_two_factor_rotatable_design_has_factorial_axial_and_center_points(self) -> None:
        result = central_composite_design(
            [FactorDefinition("A", 10, 20), FactorDefinition("B", 100, 200)],
            center_points=5,
            randomize=False,
        )

        rows = result.tables["design"]
        self.assertEqual(len(rows), 13)
        self.assertAlmostEqual(result.diagnostics["alpha"], sqrt(2.0))
        self.assertEqual(
            [row["point_type"] for row in rows].count("factorial"), 4
        )
        self.assertEqual([row["point_type"] for row in rows].count("axial"), 4)
        self.assertEqual([row["point_type"] for row in rows].count("center"), 5)
        self.assertLess(rows[4]["actual"]["A"], 10.0)
        self.assertTrue(result.diagnostics["rotatable"])

    def test_face_centered_axial_points_stay_at_supplied_levels(self) -> None:
        result = central_composite_design(
            [FactorDefinition("A", 10, 20), FactorDefinition("B", 100, 200)],
            design_type="face_centered",
            center_points=1,
            randomize=False,
        )

        self.assertEqual(result.diagnostics["alpha"], 1.0)
        axial = [row for row in result.tables["design"] if row["point_type"] == "axial"]
        self.assertTrue(
            all(
                10.0 <= row["actual"]["A"] <= 20.0
                and 100.0 <= row["actual"]["B"] <= 200.0
                for row in axial
            )
        )
        self.assertFalse(result.diagnostics["rotatable"])


class CentralCompositeAnalysisTests(unittest.TestCase):
    def test_complete_quadratic_model_recovers_hand_fixture(self) -> None:
        factors = [FactorDefinition("A", 0, 10), FactorDefinition("B", 0, 20)]
        design = central_composite_design(factors, center_points=5, randomize=False)
        responses = []
        for row in design.tables["design"]:
            a = row["coded"]["A"]
            b = row["coded"]["B"]
            responses.append(10 + 2 * a - 3 * b + 4 * a * b + 5 * a * a - 2 * b * b)

        result = analyze_central_composite(
            factors,
            responses,
            response_name="Yield",
            center_points=5,
            randomize=False,
        )

        coefficients = {
            row["term"]: row["coefficient"] for row in result.tables["coefficients"]
        }
        expected = {
            "Constant": 10.0,
            "A": 2.0,
            "B": -3.0,
            "A*B": 4.0,
            "A^2": 5.0,
            "B^2": -2.0,
        }
        for term, value in expected.items():
            self.assertAlmostEqual(coefficients[term], value)
        self.assertAlmostEqual(result.diagnostics["r_squared"], 1.0)
        self.assertEqual(result.diagnostics["pure_error_degrees_of_freedom"], 4)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_rejects_response_count_mismatch(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            analyze_central_composite(
                [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)],
                [1, 2, 3],
                randomize=False,
            )
        self.assertEqual(context.exception.detail.code, "response_count_mismatch")


class CentralCompositeSurfaceTests(unittest.TestCase):
    def test_classifies_in_region_maximum_and_builds_accessible_grid(self) -> None:
        factors = [FactorDefinition("A", 0, 10), FactorDefinition("B", 0, 20)]
        design = central_composite_design(factors, center_points=5, randomize=False)
        responses = []
        for row in design.tables["design"]:
            a = row["coded"]["A"]
            b = row["coded"]["B"]
            responses.append(100 - 2 * (a - 0.25) ** 2 - 4 * (b + 0.5) ** 2)

        result = explore_central_composite_surface(
            factors,
            responses,
            response_name="Yield",
            center_points=5,
            randomize=False,
            plot_factors=["A", "B"],
            grid_size=21,
        )

        stationary = result.tables["stationary_point"][0]
        self.assertEqual(stationary["classification"], "maximum")
        self.assertTrue(stationary["inside_factorial_cube"])
        self.assertAlmostEqual(stationary["coded"]["A"], 0.25)
        self.assertAlmostEqual(stationary["coded"]["B"], -0.5)
        self.assertAlmostEqual(stationary["actual"]["A"], 6.25)
        self.assertAlmostEqual(stationary["actual"]["B"], 5.0)
        self.assertAlmostEqual(stationary["predicted_response"], 100.0)
        self.assertEqual(len(result.tables["surface_grid"]), 441)
        for observed, expected in zip(
            result.diagnostics["canonical_eigenvalues"], [-4.0, -2.0], strict=True
        ):
            self.assertAlmostEqual(observed, expected)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_mixed_canonical_eigenvalues_classify_saddle(self) -> None:
        factors = [FactorDefinition("A", -1, 1), FactorDefinition("B", -1, 1)]
        design = central_composite_design(factors, center_points=5, randomize=False)
        responses = [
            10 + row["coded"]["A"] ** 2 - row["coded"]["B"] ** 2
            for row in design.tables["design"]
        ]

        result = explore_central_composite_surface(
            factors, responses, center_points=5, randomize=False, grid_size=5
        )

        self.assertEqual(result.diagnostics["stationary_classification"], "saddle")
        self.assertTrue(result.diagnostics["stationary_point_available"])

    def test_interaction_coefficient_uses_half_value_in_symmetric_matrix(self) -> None:
        factors = [FactorDefinition("A", -1, 1), FactorDefinition("B", -1, 1)]
        design = central_composite_design(factors, center_points=5, randomize=False)
        responses = [
            10 + 2 * row["coded"]["A"] * row["coded"]["B"]
            for row in design.tables["design"]
        ]

        result = explore_central_composite_surface(
            factors, responses, center_points=5, randomize=False, grid_size=5
        )

        for observed, expected in zip(
            result.diagnostics["canonical_eigenvalues"], [-1.0, 1.0], strict=True
        ):
            self.assertAlmostEqual(observed, expected)
        self.assertEqual(result.diagnostics["stationary_classification"], "saddle")

    def test_rejects_even_surface_grid(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            explore_central_composite_surface(
                [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)],
                [0] * 13,
                randomize=False,
                grid_size=20,
            )
        self.assertEqual(context.exception.detail.code, "invalid_grid_size")

    def test_linear_surface_generates_expected_vertical_contours(self) -> None:
        factors = [FactorDefinition("A", 0, 10), FactorDefinition("B", 0, 20)]
        design = central_composite_design(factors, center_points=5, randomize=False)
        responses = [row["coded"]["A"] for row in design.tables["design"]]

        result = explore_central_composite_surface(
            factors,
            responses,
            center_points=5,
            randomize=False,
            grid_size=5,
            contour_levels=3,
        )

        segments = result.tables["surface_contours"]
        self.assertEqual(result.diagnostics["contour_level_count"], 3)
        self.assertEqual(len(segments), 12)
        self.assertEqual({round(row["level"], 8) for row in segments}, {-0.5, 0.0, 0.5})
        for row in segments:
            self.assertAlmostEqual(row["x1_coded"], row["level"])
            self.assertAlmostEqual(row["x2_coded"], row["level"])

    def test_rejects_excessive_contour_level_count(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            explore_central_composite_surface(
                [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)],
                [0] * 13,
                randomize=False,
                contour_levels=13,
            )
        self.assertEqual(context.exception.detail.code, "invalid_contour_levels")


class PlackettBurmanDesignTests(unittest.TestCase):
    def test_12_run_design_matches_published_seed_and_is_orthogonal(self) -> None:
        factors = [FactorDefinition(f"X{index}", 0, 10) for index in range(1, 12)]
        result = plackett_burman_design(factors, runs=12, randomize=False)
        rows = result.tables["design"]

        self.assertEqual(
            list(rows[0]["coded"].values()),
            [1, 1, -1, 1, 1, 1, -1, -1, -1, 1, -1],
        )
        self.assertEqual(list(rows[-1]["coded"].values()), [-1] * 11)
        self.assertTrue(result.diagnostics["balanced"])
        self.assertTrue(result.diagnostics["pairwise_orthogonal"])
        self.assertEqual(result.diagnostics["resolution_label"], "III")
        self.assertEqual(result.diagnostics["construction"], "published-cyclic-seed")
        json.dumps(result.to_dict(), allow_nan=False)

    def test_all_supported_run_counts_pass_matrix_invariants(self) -> None:
        for runs in (12, 20, 24, 28, 32, 36, 40, 44, 48):
            with self.subTest(runs=runs):
                factors = [
                    FactorDefinition(f"X{index}", -1, 1)
                    for index in range(1, runs)
                ]
                result = plackett_burman_design(
                    factors, runs=runs, randomize=False
                )
                rows = result.tables["design"]
                self.assertEqual(len(rows), runs)
                self.assertTrue(result.diagnostics["balanced"])
                self.assertTrue(result.diagnostics["pairwise_orthogonal"])
                for name in rows[0]["coded"]:
                    self.assertEqual(sum(row["coded"][name] for row in rows), 0)

    def test_auto_selects_capacity_and_preserves_replicates_centers_and_seed(self) -> None:
        factors = [FactorDefinition(f"F{index}", 0, 2) for index in range(12)]
        first = plackett_burman_design(
            factors, replicates=2, center_points=2, seed=71
        )
        second = plackett_burman_design(
            factors, replicates=2, center_points=2, seed=71
        )

        self.assertEqual(first.diagnostics["base_run_count"], 20)
        self.assertEqual(first.diagnostics["total_run_count"], 42)
        self.assertEqual(first.tables["design"], second.tables["design"])
        centers = [row for row in first.tables["design"] if row["point_type"] == "center"]
        self.assertEqual(len(centers), 2)
        self.assertEqual(set(centers[0]["coded"].values()), {0})
        self.assertEqual(set(centers[0]["actual"].values()), {1.0})

    def test_rejects_unsupported_runs_and_insufficient_capacity(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)]
        with self.assertRaises(AnalysisInputError) as run_context:
            plackett_burman_design(factors, runs=16)
        self.assertEqual(run_context.exception.detail.code, "unsupported_runs")

        crowded = [FactorDefinition(f"X{index}", 0, 1) for index in range(12)]
        with self.assertRaises(AnalysisInputError) as capacity_context:
            plackett_burman_design(crowded, runs=12)
        self.assertEqual(
            capacity_context.exception.detail.code, "too_many_factors_for_runs"
        )


class PlackettBurmanAnalysisTests(unittest.TestCase):
    def test_saturated_design_estimates_effects_and_uses_lenth_screening(self) -> None:
        factors = [FactorDefinition(name, 0, 10) for name in "ABCDEFGHIJK"]
        design = plackett_burman_design(factors, runs=12, randomize=False)
        coefficients = [10, 4, 0.2, -0.2, 0.1, -0.1, 0.15, -0.15, 0.05, -0.05, 0.08]
        responses = [
            100 + sum(coefficient * row["coded"][name] for coefficient, name in zip(coefficients, "ABCDEFGHIJK", strict=True))
            for row in design.tables["design"]
        ]

        result = analyze_plackett_burman(
            factors, responses, runs=12, randomize=False, response_name="Yield"
        )

        effects = {row["term"]: row for row in result.tables["coefficients"]}
        self.assertAlmostEqual(effects["A"]["effect"], 20.0)
        self.assertAlmostEqual(effects["B"]["effect"], 8.0)
        self.assertTrue(effects["A"]["significant"])
        self.assertTrue(effects["B"]["significant"])
        self.assertFalse(effects["C"]["significant"])
        self.assertEqual(result.diagnostics["inference_method"], "lenth_pse")
        self.assertEqual(result.diagnostics["residual_degrees_of_freedom"], 0)
        self.assertGreater(result.diagnostics["lenth_pse"], 0)
        self.assertEqual(
            [row["factor"] for row in result.tables["confirmation_candidates"]],
            ["A", "B"],
        )
        self.assertEqual(result.tables["confirmation_candidates"][0]["suggested_level"], 10)
        self.assertEqual(result.plots["pareto"]["scale"], "effect")
        json.dumps(result.to_dict(), allow_nan=False)

    def test_unsaturated_design_uses_residual_error_and_reports_curvature(self) -> None:
        factors = [FactorDefinition(name, -1, 1) for name in "ABC"]
        design = plackett_burman_design(
            factors, runs=12, center_points=2, randomize=False
        )
        responses = [
            50 + 8 * row["coded"]["A"] - 3 * row["coded"]["B"]
            + (4 if row["point_type"] == "center" else 0)
            for row in design.tables["design"]
        ]

        result = analyze_plackett_burman(
            factors,
            responses,
            runs=12,
            center_points=2,
            randomize=False,
        )

        self.assertEqual(result.diagnostics["inference_method"], "residual_error")
        self.assertEqual(result.diagnostics["residual_degrees_of_freedom"], 10)
        self.assertEqual(result.plots["pareto"]["scale"], "standardized_effect")
        self.assertAlmostEqual(result.tables["curvature"][0]["difference"], 4.0)
        self.assertEqual(len(result.tables["residuals"]), 14)

    def test_rejects_response_count_and_invalid_alpha(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)]
        with self.assertRaises(AnalysisInputError) as count_context:
            analyze_plackett_burman(factors, [1, 2], runs=12, randomize=False)
        self.assertEqual(count_context.exception.detail.code, "response_count_mismatch")

        with self.assertRaises(AnalysisInputError) as alpha_context:
            analyze_plackett_burman(
                factors, list(range(12)), runs=12, randomize=False, alpha=0.9
            )
        self.assertEqual(alpha_context.exception.detail.code, "invalid_alpha")


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


class FullFactorialDesirabilityTests(unittest.TestCase):
    def test_individual_and_composite_desirability_match_hand_calculation(self) -> None:
        maximize = individual_desirability(
            75, goal="maximize", lower=50, target=100, weight=1
        )
        minimize = individual_desirability(
            25, goal="minimize", target=0, upper=100, weight=1
        )
        target = individual_desirability(
            60, goal="target", lower=0, target=50, upper=100, weight=2
        )

        self.assertAlmostEqual(maximize, 0.5)
        self.assertAlmostEqual(minimize, 0.75)
        self.assertAlmostEqual(target, 0.64)
        self.assertAlmostEqual(
            composite_desirability([maximize, minimize], [1, 3]),
            (0.5 * 0.75**3) ** 0.25,
        )

    def test_multiple_responses_find_joint_vertex_solution(self) -> None:
        result = optimize_full_factorial_desirability(
            [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)],
            [
                ResponseObjective(
                    name="Yield",
                    responses=[0, 10, 0, 10],
                    goal="maximize",
                    lower=0,
                    target=10,
                ),
                ResponseObjective(
                    name="Cost",
                    responses=[0, 0, 10, 10],
                    goal="minimize",
                    target=0,
                    upper=10,
                    importance=2,
                ),
            ],
            randomize=False,
            interaction_order=1,
        )

        solution = result.tables["solution"][0]
        self.assertEqual(solution["actual"], {"A": 1.0, "B": 0.0})
        self.assertAlmostEqual(solution["composite_desirability"], 1.0)
        self.assertEqual(
            [row["desirability"] for row in result.tables["response_desirabilities"]],
            [1.0, 1.0],
        )
        self.assertFalse(result.diagnostics["global_optimum_proven"])
        json.dumps(result.to_dict(), allow_nan=False)

    def test_target_objective_can_find_interior_setting(self) -> None:
        result = optimize_full_factorial_desirability(
            [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)],
            [
                ResponseObjective(
                    name="Dimension",
                    responses=[0, 10, 0, 10],
                    goal="target",
                    lower=0,
                    target=5,
                    upper=10,
                )
            ],
            randomize=False,
            interaction_order=1,
        )

        solution = result.tables["solution"][0]
        self.assertAlmostEqual(solution["actual"]["A"], 0.5, places=6)
        self.assertAlmostEqual(solution["composite_desirability"], 1.0)

    def test_rejects_invalid_objective_boundaries_and_response_identity(self) -> None:
        factors = [FactorDefinition("A", 0, 1), FactorDefinition("B", 0, 1)]
        with self.assertRaises(AnalysisInputError) as count_context:
            optimize_full_factorial_desirability(
                factors,
                [
                    ResponseObjective(
                        name="Yield",
                        responses=[1, 2, 3],
                        goal="maximize",
                        lower=0,
                        target=5,
                    )
                ],
                randomize=False,
            )
        self.assertEqual(count_context.exception.detail.code, "response_count_mismatch")

        with self.assertRaises(AnalysisInputError) as bound_context:
            optimize_full_factorial_desirability(
                factors,
                [
                    ResponseObjective(
                        name="Yield",
                        responses=[1, 2, 3, 4],
                        goal="maximize",
                        target=10,
                    )
                ],
                randomize=False,
            )
        self.assertEqual(bound_context.exception.detail.code, "missing_desirability_bound")

        duplicate = ResponseObjective(
            name="Y",
            responses=[1, 2, 3, 4],
            goal="maximize",
            lower=0,
            target=5,
        )
        with self.assertRaises(AnalysisInputError) as name_context:
            optimize_full_factorial_desirability(
                factors, [duplicate, duplicate], randomize=False
            )
        self.assertEqual(name_context.exception.detail.code, "duplicate_response_name")
