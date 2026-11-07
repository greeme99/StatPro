from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.analyses.msa import AttributeAssessmentRecord, attribute_agreement
from statpro.domain.errors import AnalysisInputError


def records() -> list[AttributeAssessmentRecord]:
    return [
        AttributeAssessmentRecord("I1", "A", 1, "good", "good"),
        AttributeAssessmentRecord("I1", "A", 2, "good", "good"),
        AttributeAssessmentRecord("I1", "B", 1, "good", "good"),
        AttributeAssessmentRecord("I1", "B", 2, "bad", "good"),
        AttributeAssessmentRecord("I2", "A", 1, "bad", "bad"),
        AttributeAssessmentRecord("I2", "A", 2, "bad", "bad"),
        AttributeAssessmentRecord("I2", "B", 1, "bad", "bad"),
        AttributeAssessmentRecord("I2", "B", 2, "bad", "bad"),
    ]


class AttributeAgreementTests(unittest.TestCase):
    def test_reports_within_and_standard_agreement(self) -> None:
        result = attribute_agreement(records())
        rows = {row["appraiser"]: row for row in result.tables["appraiser_agreement"]}

        self.assertEqual(result.analysis_type, "msa.attribute_agreement")
        self.assertEqual(rows["A"]["within_percent"], 100.0)
        self.assertEqual(rows["A"]["standard_percent"], 100.0)
        self.assertEqual(rows["B"]["within_percent"], 50.0)
        self.assertEqual(rows["B"]["standard_percent"], 50.0)
        self.assertIn("Cohen", result.warnings[0])

    def test_rejects_missing_crossed_assessment(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            attribute_agreement(records()[:-1])
        self.assertEqual(context.exception.detail.code, "unbalanced_attribute_trials")
