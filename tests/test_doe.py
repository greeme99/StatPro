from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.doe import FactorDefinition, full_factorial_2level
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
