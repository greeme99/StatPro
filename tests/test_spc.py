from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.spc import (
    c_chart,
    individuals_moving_range,
    nelson_signals,
    np_chart,
    p_chart,
    u_chart,
    western_electric_signals,
    xbar_r,
    xbar_s,
)
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

    def test_western_electric_and_trend_rules_match_published_windows(self) -> None:
        fixtures = {
            "WECO-1": [3.1],
            "WECO-2": [2.1, 0.0, 2.2],
            "WECO-3": [1.1, 1.2, 0.0, 1.3, 1.4],
            "WECO-4": [0.1] * 8,
            "TREND-6": [1, 2, 3, 4, 5, 6],
            "ALTERNATING-14": [1 if index % 2 == 0 else -1 for index in range(14)],
        }
        for expected, values in fixtures.items():
            with self.subTest(rule=expected):
                signals = western_electric_signals(values, center=0.0, sigma=1.0)
                self.assertIn(expected, {signal["rule"] for signal in signals})

    def test_nelson_rules_match_public_special_cause_windows(self) -> None:
        fixtures = {
            "NELSON-1": [3.1],
            "NELSON-2": [0.1] * 9,
            "NELSON-3": [1, 2, 3, 4, 5, 6],
            "NELSON-4": [1 if index % 2 == 0 else -1 for index in range(14)],
            "NELSON-5": [2.1, 0.0, 2.2],
            "NELSON-6": [1.1, 1.2, 0.0, 1.3, 1.4],
            "NELSON-7": [0.5 if index % 2 == 0 else -0.5 for index in range(15)],
            "NELSON-8": [1.1 if index % 2 == 0 else -1.1 for index in range(8)],
        }
        for expected, values in fixtures.items():
            with self.subTest(rule=expected):
                signals = nelson_signals(values, center=0.0, sigma=1.0)
                self.assertIn(expected, {signal["rule"] for signal in signals})

    def test_nelson_pattern_only_rules_do_not_require_sigma(self) -> None:
        signals = nelson_signals(
            [1, 2, 3, 4, 5, 6],
            center=0.0,
            sigma=None,
            enabled_rules=(3,),
        )

        self.assertEqual({signal["rule"] for signal in signals}, {"NELSON-3"})

    def test_imr_nelson_rule_set_preserves_rule_events(self) -> None:
        result = individuals_moving_range([1, 2, 3, 4, 5, 6], rules="nelson")

        self.assertIn(
            "NELSON-3",
            {signal["rule"] for signal in result.diagnostics["individual_rule_signals"]},
        )
        self.assertEqual(result.parameters["rules"], "nelson")

    def test_rule_set_can_be_bounded_to_basic_limits(self) -> None:
        values = [1, 2, 3, 4, 5, 6]
        western = individuals_moving_range(values, rules="western_electric")
        basic = individuals_moving_range(values, rules="basic")

        self.assertIn(
            "TREND-6",
            {signal["rule"] for signal in western.diagnostics["individual_rule_signals"]},
        )
        self.assertEqual(basic.diagnostics["individual_rule_signals"], [])
        self.assertNotEqual(western.input_digest, basic.input_digest)

    def test_rejects_unknown_control_rule_set(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            individuals_moving_range([1, 2, 3], rules="nelson-all")
        self.assertEqual(context.exception.detail.code, "invalid_control_rule_set")


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

    def test_nelson_rules_apply_all_tests_to_xbar_and_one_through_four_to_range(self) -> None:
        xbar_trend = xbar_r(
            [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]],
            rules="nelson",
        )
        range_trend = xbar_r(
            [[-0.5, 0.5], [-1, 1], [-1.5, 1.5], [-2, 2], [-2.5, 2.5], [-3, 3]],
            rules="nelson",
        )

        self.assertIn(
            "NELSON-3",
            {signal["rule"] for signal in xbar_trend.diagnostics["xbar_rule_signals"]},
        )
        self.assertIn(
            "NELSON-3",
            {signal["rule"] for signal in range_trend.diagnostics["range_rule_signals"]},
        )
        self.assertTrue(
            all(
                int(signal["rule"].split("-")[1]) <= 4
                for signal in range_trend.diagnostics["range_rule_signals"]
            )
        )

    def test_xbar_r_rejects_unknown_control_rule_set(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            xbar_r([[1, 2], [3, 4]], rules="western_electric")
        self.assertEqual(context.exception.detail.code, "invalid_control_rule_set")


class XbarSTests(unittest.TestCase):
    def test_c4_limits_match_public_xbar_s_formulas(self) -> None:
        result = xbar_s([list(range(1, 11)), list(range(2, 12))])
        xbar_limits = result.tables["limits"]["xbar"]
        s_limits = result.tables["limits"]["standard_deviation"]

        self.assertEqual(result.analysis_type, "spc.xbar_s")
        self.assertAlmostEqual(result.parameters["c4"], 0.9726592741)
        self.assertAlmostEqual(result.parameters["a3"], 0.9753500771)
        self.assertAlmostEqual(result.parameters["b3"], 0.2837056576, places=6)
        self.assertAlmostEqual(result.parameters["b4"], 1.7162943424, places=6)
        self.assertAlmostEqual(xbar_limits["center"], 6.0)
        self.assertAlmostEqual(s_limits["center"], 3.0276503541)
        self.assertAlmostEqual(result.diagnostics["estimated_sigma"], 3.1127553447)

    def test_rejects_unequal_subgroups(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            xbar_s([[1, 2, 3], [4, 5]])
        self.assertEqual(context.exception.detail.code, "unequal_subgroup_size")

    def test_small_subgroups_are_calculated_with_method_warning(self) -> None:
        result = xbar_s([[1, 2, 3], [2, 3, 4]])
        self.assertTrue(any("below 9" in warning for warning in result.warnings))

    def test_nelson_rules_apply_one_through_four_to_s_chart(self) -> None:
        result = xbar_s(
            [
                [index + offset for offset in range(10)]
                for index in range(8)
            ],
            rules="nelson",
        )
        self.assertTrue(
            all(
                int(signal["rule"].split("-")[1]) <= 4
                for signal in result.diagnostics["standard_deviation_rule_signals"]
            )
        )

    def test_zero_within_subgroup_variation_keeps_xbar_limit_signals(self) -> None:
        result = xbar_s([[1.0] * 10, [2.0] * 10])

        self.assertEqual(result.plots["xbar"]["signals"], [0, 1])
        self.assertEqual(result.diagnostics["xbar_limit_signal_indices"], [0, 1])
        self.assertEqual(result.plots["standard_deviation"]["signals"], [])


class AttributeChartTests(unittest.TestCase):
    def test_p_chart_uses_pooled_center_and_per_subgroup_limits(self) -> None:
        result = p_chart([5, 8, 12], [100, 200, 100])
        points = result.tables["chart_points"]

        self.assertEqual(result.analysis_type, "spc.p_chart")
        self.assertAlmostEqual(result.tables["summary"]["pooled_proportion"], 0.0625)
        self.assertAlmostEqual(points[0]["statistic"], 0.05)
        self.assertAlmostEqual(points[1]["statistic"], 0.04)
        self.assertLess(points[1]["ucl"], points[0]["ucl"])
        self.assertEqual(result.parameters["sample_size_mode"], "variable")

    def test_p_chart_flags_a_point_outside_its_three_sigma_limit(self) -> None:
        result = p_chart([2, 3, 2, 3, 25], [100, 100, 100, 100, 100])

        self.assertEqual(result.diagnostics["signal_indices"], [4])
        self.assertTrue(result.tables["chart_points"][4]["signal"])

    def test_np_chart_uses_count_scale_and_constant_sample_size(self) -> None:
        result = np_chart([2, 3, 2, 3, 25], [100, 100, 100, 100, 100])
        point = result.tables["chart_points"][0]

        self.assertEqual(result.analysis_type, "spc.np_chart")
        self.assertAlmostEqual(point["center"], 7.0)
        self.assertEqual(point["statistic"], 2.0)
        self.assertEqual(result.diagnostics["signal_indices"], [4])

    def test_np_chart_rejects_variable_sample_sizes(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            np_chart([2, 3], [100, 120])
        self.assertEqual(context.exception.detail.code, "unequal_sample_size")

    def test_attribute_charts_reject_invalid_counts(self) -> None:
        cases = [
            (([1.5, 2], [100, 100]), "invalid_count"),
            (([1, 2], [100, 0]), "invalid_sample_size"),
            (([101, 2], [100, 100]), "count_exceeds_sample_size"),
            (([1, 2], [100]), "mismatched_subgroups"),
        ]
        for arguments, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(AnalysisInputError) as context:
                    p_chart(*arguments)
                self.assertEqual(context.exception.detail.code, code)

    def test_attribute_chart_digest_normalizes_equivalent_integer_inputs(self) -> None:
        first = p_chart([1, 2], [100, 100])
        second = p_chart([1.0, 2.0], [100.0, 100.0])

        self.assertEqual(first.input_digest, second.input_digest)

    def test_c_chart_uses_poisson_count_limits(self) -> None:
        result = c_chart([1, 2, 1, 2, 12])
        point = result.tables["chart_points"][0]

        self.assertEqual(result.analysis_type, "spc.c_chart")
        self.assertAlmostEqual(point["center"], 3.6)
        self.assertAlmostEqual(point["ucl"], 3.6 + 3.0 * math.sqrt(3.6))
        self.assertEqual(result.diagnostics["signal_indices"], [4])

    def test_u_chart_uses_weighted_rate_and_variable_opportunity(self) -> None:
        result = u_chart([1, 2, 1, 2, 12], [1, 2, 1, 2, 2])
        point = result.tables["chart_points"][1]

        self.assertEqual(result.analysis_type, "spc.u_chart")
        self.assertAlmostEqual(result.tables["summary"]["average_defects_per_unit"], 2.25)
        self.assertAlmostEqual(point["statistic"], 1.0)
        self.assertEqual(result.parameters["opportunity_mode"], "variable")

    def test_c_chart_rejects_unequal_inspection_opportunity(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            c_chart([1, 2], [1, 2])
        self.assertEqual(context.exception.detail.code, "unequal_opportunity")

    def test_u_chart_rejects_nonpositive_inspection_units(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            u_chart([1, 2], [1, 0])
        self.assertEqual(context.exception.detail.code, "invalid_inspection_units")


if __name__ == "__main__":
    unittest.main()
