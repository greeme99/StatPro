from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.dmaic.cost_benefit import CostBenefitItem, summarize_cost_benefit
from statpro.dmaic.models import DmaicInputError


class CostBenefitTests(unittest.TestCase):
    def test_summary_keeps_input_based_roi_and_payback_separate_from_realization(self) -> None:
        summary = summarize_cost_benefit(
            costs=(CostBenefitItem("Fixture", 1200, "one_time"), CostBenefitItem("Maintenance", 50, "monthly")),
            benefits=(CostBenefitItem("Reduced scrap", 300, "monthly"),), analysis_months=12,
        )
        self.assertEqual(summary["cost_total"], 1800)
        self.assertEqual(summary["benefit_total"], 3600)
        self.assertEqual(summary["net_benefit"], 1800)
        self.assertEqual(summary["roi_percent"], 100)
        self.assertEqual(summary["estimated_payback_months"], 4)

    def test_rejects_invalid_amount_or_period(self) -> None:
        with self.assertRaises(DmaicInputError):
            summarize_cost_benefit(costs=(CostBenefitItem("Fixture", -1, "one_time"),), benefits=(CostBenefitItem("Benefit", 1, "monthly"),), analysis_months=12)
        with self.assertRaises(DmaicInputError):
            summarize_cost_benefit(costs=(CostBenefitItem("Fixture", 1, "one_time"),), benefits=(CostBenefitItem("Benefit", 1, "monthly"),), analysis_months=0)
