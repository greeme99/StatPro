from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.quality_tools import (
    CheckSheetInputError,
    CheckSheetSnapshot,
    add_check_sheet_record,
    create_check_sheet,
    summarize_check_sheet,
)


class CheckSheetTests(unittest.TestCase):
    def test_records_create_an_immutable_revision_and_ranked_summary(self) -> None:
        original = create_check_sheet(
            sheet_id="line-a",
            title="외관 불량",
            process_name="조립",
            category_label="불량 유형",
        )
        revised = add_check_sheet_record(original, record_id="r1", category="스크래치", count=3)
        revised = add_check_sheet_record(revised, record_id="r2", category="오염", count=1)
        result = summarize_check_sheet(revised)
        self.assertEqual(original.records, ())
        self.assertEqual(revised.revision, 3)
        self.assertEqual(result.tables["summary"], {"total": 4, "category_count": 2})
        self.assertEqual(result.tables["frequencies"][0]["percentage"], 75.0)
        self.assertEqual(CheckSheetSnapshot.from_dict(revised.to_dict()), revised)

    def test_rejects_non_positive_counts_and_duplicate_record_ids(self) -> None:
        sheet = create_check_sheet(
            sheet_id="s", title="t", process_name="p", category_label="c"
        )
        with self.assertRaises(CheckSheetInputError):
            add_check_sheet_record(sheet, record_id="r", category="x", count=0)
        revised = add_check_sheet_record(sheet, record_id="r", category="x", count=1)
        with self.assertRaises(CheckSheetInputError):
            add_check_sheet_record(revised, record_id="r", category="y", count=1)


if __name__ == "__main__":
    unittest.main()
