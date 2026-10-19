from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.spc import individuals_moving_range
from statpro.domain.schema import result_bundle_schema


class ResultBundleSchemaTests(unittest.TestCase):
    def test_schema_is_valid_and_accepts_runtime_result(self) -> None:
        schema = result_bundle_schema()
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())

        document = individuals_moving_range([1, 2, 3]).to_dict()
        validator.validate(document)

    def test_schema_rejects_unknown_or_malformed_contract_fields(self) -> None:
        schema = result_bundle_schema()
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        document = copy.deepcopy(individuals_moving_range([1, 2, 3]).to_dict())
        document["input_digest"] = "not-a-digest"
        document["unexpected"] = True

        with self.assertRaises(ValidationError):
            validator.validate(document)
