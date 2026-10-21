from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.cli import main


class CliBoundaryTests(unittest.TestCase):
    def test_imr_returns_selected_supplementary_rule_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "imr.json"
            path.write_text(
                json.dumps(
                    {
                        "values": [1, 2, 3, 4, 5, 6],
                        "rules": "western_electric",
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["imr", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["parameters"]["rules"], "western_electric")
        self.assertIn(
            "TREND-6",
            [
                signal["rule"]
                for signal in response["result"]["plots"]["individuals"]["rule_signals"]
            ],
        )

    def test_xbar_r_returns_nelson_signals_for_each_chart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xbar-r.json"
            path.write_text(
                json.dumps(
                    {
                        "subgroups": [
                            [0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]
                        ],
                        "rules": "nelson",
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["xbar-r", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertIn(
            "NELSON-3",
            [
                signal["rule"]
                for signal in response["result"]["plots"]["xbar"]["rule_signals"]
            ],
        )

    def test_doe_analysis_returns_effects_anova_and_residuals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "doe-analysis.json"
            path.write_text(
                json.dumps(
                    {
                        "factors": [
                            {"name": "A", "low": 0, "high": 1},
                            {"name": "B", "low": 10, "high": 20},
                        ],
                        "responses": [10, 14, 12, 20, 12, 16, 10, 22],
                        "replicates": 2,
                        "randomize": False,
                        "interaction_order": 2,
                        "prediction_points": [{"A": 0.75, "B": 15}],
                        "optimization_goal": "maximize",
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["doe-analyze-full-factorial", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(response["ok"])
        self.assertEqual(
            response["result"]["analysis_type"],
            "doe.full_factorial_2level_analysis",
        )
        self.assertEqual(len(response["result"]["tables"]["coefficients"]), 4)
        self.assertEqual(len(response["result"]["tables"]["residuals"]), 8)
        self.assertAlmostEqual(
            response["result"]["tables"]["predictions"][0]["predicted_response"],
            16.25,
        )
        self.assertEqual(
            response["result"]["tables"]["optimization"][0]["actual"],
            {"A": 1.0, "B": 20.0},
        )

    def test_doe_response_optimizer_returns_composite_desirability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "doe-optimizer.json"
            path.write_text(
                json.dumps(
                    {
                        "factors": [
                            {"name": "A", "low": 0, "high": 1},
                            {"name": "B", "low": 0, "high": 1},
                        ],
                        "randomize": False,
                        "interaction_order": 1,
                        "objectives": [
                            {
                                "name": "Yield",
                                "responses": [0, 10, 0, 10],
                                "goal": "maximize",
                                "lower": 0,
                                "target": 10,
                            },
                            {
                                "name": "Cost",
                                "responses": [0, 0, 10, 10],
                                "goal": "minimize",
                                "target": 0,
                                "upper": 10,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["doe-optimize-responses", "--input", str(path)])

        response = json.loads(output.getvalue())
        solution = response["result"]["tables"]["solution"][0]
        self.assertEqual(exit_code, 0)
        self.assertEqual(solution["actual"], {"A": 1.0, "B": 0.0})
        self.assertAlmostEqual(solution["composite_desirability"], 1.0)

    def test_fractional_factorial_returns_alias_structure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fractional.json"
            path.write_text(
                json.dumps(
                    {
                        "factors": [
                            {"name": name, "low": 0, "high": 1} for name in "ABCD"
                        ],
                        "generators": [
                            {"factor": "D", "terms": ["A", "B", "C"]}
                        ],
                        "randomize": False,
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["doe-fractional-factorial", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(response["result"]["diagnostics"]["resolution_label"], "IV")
        self.assertEqual(len(response["result"]["tables"]["design"]), 8)

    def test_dataset_import_csv_returns_typed_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process.csv"
            path.write_text("value,label\n1,A\n2,B\n", encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["dataset-import-csv", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(response["ok"])
        self.assertEqual(response["dataset"]["row_count"], 2)
        self.assertEqual(response["dataset"]["columns"][0]["data_type"], "numeric")

    def test_malformed_factor_is_a_tagged_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-doe.json"
            path.write_text(json.dumps({"factors": [{"name": "A", "low": 0}]}), encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["doe-full-factorial", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "invalid_factor_definition")

    def test_malformed_measurement_record_is_a_tagged_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-gage.json"
            path.write_text(
                json.dumps({"records": [{"part": "P1", "operator": "A"}]}),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main(["gage-rr-crossed", "--input", str(path)])

        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "invalid_measurement_record")
