from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.normality import jarque_bera_normality
from statpro.domain.errors import AnalysisInputError


class JarqueBeraTests(unittest.TestCase):
    def test_returns_statistic_and_explicit_small_sample_warning(self) -> None:
        result = jarque_bera_normality([1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(result.analysis_type, "normality.jarque_bera")
        self.assertIn("p_value", result.diagnostics)
        self.assertTrue(result.warnings)

    def test_uses_documented_jb_formula_and_df_two_survival_function(self) -> None:
        result = jarque_bera_normality([0, 0, 0, 1])
        row = result.tables["normality"]["rows"][0]
        self.assertAlmostEqual(row["skewness"], 1.1547005383792515)
        self.assertAlmostEqual(row["kurtosis"], 2.3333333333333335)
        self.assertAlmostEqual(row["jb_statistic"], 0.962962962962963)
        self.assertAlmostEqual(row["p_value"], 0.6178673543839127)
        self.assertFalse(result.diagnostics["reject_normality"])

    def test_rejects_undefined_constant_data(self) -> None:
        with self.assertRaises(AnalysisInputError) as raised:
            jarque_bera_normality([4, 4, 4])
        self.assertEqual(raised.exception.detail.code, "zero_variation")


if __name__ == "__main__":
    unittest.main()
