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
