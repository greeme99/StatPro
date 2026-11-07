from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.msa import BiasLinearityRecord, gage_bias_linearity
from statpro.domain.errors import AnalysisInputError


def records() -> list[BiasLinearityRecord]:
    return [
        BiasLinearityRecord(10, 11),
        BiasLinearityRecord(10, 11),
        BiasLinearityRecord(20, 22),
        BiasLinearityRecord(20, 22),
        BiasLinearityRecord(30, 33),
        BiasLinearityRecord(30, 33),
    ]


class GageBiasLinearityTests(unittest.TestCase):
    def test_reports_level_bias_and_linear_fit(self) -> None:
        result = gage_bias_linearity(records())
        levels = result.tables["bias_by_reference"]
        fit = result.tables["linearity_fit"]

        self.assertEqual(result.analysis_type, "msa.gage_bias_linearity")
        self.assertEqual(levels[0]["mean_bias"], 1.0)
        self.assertEqual(levels[2]["mean_bias"], 3.0)
        self.assertAlmostEqual(fit["slope"], 0.1)
        self.assertAlmostEqual(fit["intercept"], 0.0)
        self.assertEqual(fit["r_squared"], 1.0)

    def test_rejects_reference_level_without_repetition(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            gage_bias_linearity(records()[:-1])
        self.assertEqual(context.exception.detail.code, "insufficient_reference_replicates")
