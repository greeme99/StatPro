from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed, gage_rr_nested
from statpro.domain.errors import AnalysisInputError


def fixture_records() -> list[MeasurementRecord]:
    return [
        MeasurementRecord("P1", "A", 10),
        MeasurementRecord("P1", "A", 12),
        MeasurementRecord("P1", "B", 11),
        MeasurementRecord("P1", "B", 13),
        MeasurementRecord("P2", "A", 20),
        MeasurementRecord("P2", "A", 22),
        MeasurementRecord("P2", "B", 19),
        MeasurementRecord("P2", "B", 21),
    ]


class CrossedGageRrTests(unittest.TestCase):
    def test_balanced_fixture_matches_hand_calculated_anova_and_components(self) -> None:
        result = gage_rr_crossed(fixture_records())
        anova = {row["source"]: row for row in result.tables["anova"]}
        components = {
            row["source"]: row for row in result.tables["variance_components"]
        }

        self.assertEqual(result.tables["study"]["replicates_per_cell"], 2)
        self.assertAlmostEqual(anova["part"]["ss"], 162.0)
        self.assertAlmostEqual(anova["part_operator_interaction"]["ss"], 2.0)
        self.assertAlmostEqual(anova["repeatability"]["ss"], 8.0)
        self.assertAlmostEqual(anova["total"]["ss"], 172.0)
        self.assertAlmostEqual(result.diagnostics["anova_decomposition_error"], 0.0)
        self.assertAlmostEqual(components["repeatability"]["variance"], 2.0)
        self.assertAlmostEqual(components["part_to_part"]["variance"], 40.0)
        self.assertAlmostEqual(components["total_variation"]["variance"], 42.0)
        self.assertEqual(result.diagnostics["number_of_distinct_categories"], 6)
        self.assertEqual(anova["part"]["denominator_source"], "part_operator_interaction")
        self.assertAlmostEqual(anova["part"]["f_value"], 81.0)
        self.assertGreater(anova["part"]["p_value"], 0.05)
        self.assertEqual(anova["part_operator_interaction"]["denominator_source"], "repeatability")
        self.assertAlmostEqual(anova["part_operator_interaction"]["f_value"], 1.0)
        self.assertAlmostEqual(anova["part_operator_interaction"]["p_value"], 0.3739009663)
        self.assertFalse(anova["part"]["significant"])
        repeatability_ci = components["repeatability"]["variance_confidence_interval"]
        self.assertEqual(repeatability_ci["confidence_level"], 0.95)
        self.assertAlmostEqual(repeatability_ci["lower"], 0.7179, places=3)
        self.assertAlmostEqual(repeatability_ci["upper"], 16.5146, places=3)

    def test_negative_component_is_truncated_but_raw_estimate_is_preserved(self) -> None:
        result = gage_rr_crossed(fixture_records())
        components = {
            row["source"]: row for row in result.tables["variance_components"]
        }

        self.assertAlmostEqual(result.diagnostics["raw_variance_estimates"]["operator"], -0.5)
        self.assertEqual(components["operator"]["variance"], 0.0)
        self.assertTrue(any("operator" in warning for warning in result.warnings))

    def test_rejects_missing_crossed_cell(self) -> None:
        records = [
            record
            for record in fixture_records()
            if not (record.part == "P2" and record.operator == "B")
        ]
        with self.assertRaises(AnalysisInputError) as context:
            gage_rr_crossed(records)
        self.assertEqual(context.exception.detail.code, "incomplete_crossed_design")

    def test_rejects_unbalanced_replicates(self) -> None:
        records = fixture_records()[:-1]
        with self.assertRaises(AnalysisInputError) as context:
            gage_rr_crossed(records)
        self.assertEqual(context.exception.detail.code, "unbalanced_design")


class NestedGageRrTests(unittest.TestCase):
    def test_balanced_nested_design_reports_nested_anova_and_components(self) -> None:
        records = [
            MeasurementRecord("A1", "A", 10), MeasurementRecord("A1", "A", 12),
            MeasurementRecord("A2", "A", 20), MeasurementRecord("A2", "A", 22),
            MeasurementRecord("B1", "B", 12), MeasurementRecord("B1", "B", 14),
            MeasurementRecord("B2", "B", 18), MeasurementRecord("B2", "B", 20),
        ]
        result = gage_rr_nested(records)
        anova = {row["source"]: row for row in result.tables["anova"]}
        components = {row["source"]: row for row in result.tables["variance_components"]}

        self.assertEqual(result.analysis_type, "msa.gage_rr_nested")
        self.assertEqual(result.tables["study"]["parts_per_operator"], 2)
        self.assertEqual(result.tables["study"]["replicates_per_part"], 2)
        self.assertEqual(components["repeatability"]["variance"], 2.0)
        self.assertEqual(components["operator"]["variance"], 0.0)
        self.assertEqual(components["part_to_part"]["variance"], 33.0)
        self.assertEqual(anova["operator"]["denominator_source"], "part_operator")
        self.assertAlmostEqual(anova["operator"]["f_value"], 0.0)
        self.assertAlmostEqual(anova["operator"]["p_value"], 1.0)
        self.assertEqual(anova["part_operator"]["denominator_source"], "repeatability")
        self.assertAlmostEqual(anova["part_operator"]["f_value"], 34.0)
        self.assertLess(anova["part_operator"]["p_value"], 0.05)
        self.assertTrue(anova["part_operator"]["significant"])
        repeatability_ci = components["repeatability"]["variance_confidence_interval"]
        self.assertLess(repeatability_ci["lower"], 2.0)
        self.assertGreater(repeatability_ci["upper"], 2.0)

    def test_rejects_part_shared_between_operators(self) -> None:
        records = [
            MeasurementRecord("P1", "A", 10), MeasurementRecord("P1", "A", 11),
            MeasurementRecord("P2", "A", 20), MeasurementRecord("P2", "A", 21),
            MeasurementRecord("P1", "B", 30), MeasurementRecord("P1", "B", 31),
            MeasurementRecord("P3", "B", 40), MeasurementRecord("P3", "B", 41),
        ]
        with self.assertRaises(AnalysisInputError) as context:
            gage_rr_nested(records)
        self.assertEqual(context.exception.detail.code, "part_not_nested")
