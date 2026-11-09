from __future__ import annotations

import sys
import tempfile
import unittest
import io
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.domain.data import (
    DataType,
    add_derived_numeric_column,
    create_worksheet,
    filter_worksheet_rows,
    import_csv_bytes,
    import_csv_dataset,
    import_xlsx_bytes,
    replace_worksheet_cell,
    sort_worksheet_rows,
)
from statpro.domain.errors import AnalysisInputError


class DatasetImportTests(unittest.TestCase):
    @staticmethod
    def _xlsx_bytes(*, formula: bool = False) -> bytes:
        cell = '<c r="A2"><f>1+1</f><v>2</v></c>' if formula else '<c r="A2"><v>10.5</v></c>'
        parts = {
            "xl/workbook.xml": (
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Measurements" sheetId="1" r:id="rId1"/></sheets></workbook>'
            ),
            "xl/_rels/workbook.xml.rels": (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/></Relationships>'
            ),
            "xl/sharedStrings.xml": (
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<si><t>value</t></si><si><t>accepted</t></si><si><t>ok</t></si></sst>'
            ),
            "xl/worksheets/sheet1.xml": (
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
                f'<row r="2">{cell}<c r="B2" t="b"><v>1</v></c></row>'
                '<row r="3"><c r="B3" t="b"><v>0</v></c></row>'
                '</sheetData></worksheet>'
            ),
        }
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, content in parts.items():
                archive.writestr(path, content)
        return stream.getvalue()

    def test_csv_bytes_preserve_caller_source_identity_without_a_temp_file(self) -> None:
        source = b"value,accepted\n10.5,true\n,false\n"
        dataset = import_csv_bytes(source, location="browser-upload.csv")

        self.assertEqual(dataset.source.location, "browser-upload.csv")
        self.assertEqual(dataset.source.kind, "csv")
        self.assertEqual(dataset.row_count, 2)
        self.assertEqual(dataset.columns[0].values, (10.5, None))

    def test_csv_import_infers_types_and_preserves_missing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process.csv"
            path.write_text(
                "value,accepted,measured_at,note\n"
                "10.5,true,2026-10-19T10:00:00,ok\n"
                ",false,2026-10-19T11:00:00,check\n",
                encoding="utf-8",
            )
            dataset = import_csv_dataset(path)

        columns = {column.name: column for column in dataset.columns}
        self.assertEqual(dataset.row_count, 2)
        self.assertEqual(columns["value"].data_type, DataType.NUMERIC)
        self.assertEqual(columns["value"].values, (10.5, None))
        self.assertEqual(columns["accepted"].data_type, DataType.LOGICAL)
        self.assertEqual(columns["measured_at"].data_type, DataType.DATETIME)
        self.assertEqual(columns["note"].data_type, DataType.TEXT)
        self.assertEqual(len(dataset.digest), 64)
        self.assertEqual(len(dataset.source.content_digest), 64)

    def test_xlsx_values_from_first_sheet_preserve_types_and_missing_values(self) -> None:
        dataset = import_xlsx_bytes(self._xlsx_bytes(), location="process.xlsx")

        columns = {column.name: column for column in dataset.columns}
        self.assertEqual(dataset.source.kind, "xlsx")
        self.assertEqual(dataset.source.location, "process.xlsx")
        self.assertEqual(dataset.row_count, 2)
        self.assertEqual(columns["value"].data_type, DataType.NUMERIC)
        self.assertEqual(columns["value"].values, (10.5, None))
        self.assertEqual(columns["accepted"].data_type, DataType.LOGICAL)
        self.assertEqual(columns["accepted"].values, (True, False))

    def test_xlsx_formula_cells_are_rejected_without_evaluation(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            import_xlsx_bytes(self._xlsx_bytes(formula=True), location="formula.xlsx")

        self.assertEqual(context.exception.detail.code, "xlsx_formula_not_supported")

    def test_normalized_digest_is_independent_of_file_location(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.csv"
            second = Path(directory) / "second.csv"
            content = "x,y\n1,A\n2,B\n"
            first.write_text(content, encoding="utf-8")
            second.write_text(content, encoding="utf-8")

            first_dataset = import_csv_dataset(first)
            second_dataset = import_csv_dataset(second)

        self.assertEqual(first_dataset.digest, second_dataset.digest)
        self.assertEqual(first_dataset.source.content_digest, second_dataset.source.content_digest)
        self.assertNotEqual(first_dataset.source.location, second_dataset.source.location)

    def test_rejects_duplicate_headers_and_ragged_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.csv"
            duplicate.write_text("x,x\n1,2\n", encoding="utf-8")
            ragged = Path(directory) / "ragged.csv"
            ragged.write_text("x,y\n1\n", encoding="utf-8")

            with self.assertRaises(AnalysisInputError) as duplicate_context:
                import_csv_dataset(duplicate)
            with self.assertRaises(AnalysisInputError) as ragged_context:
                import_csv_dataset(ragged)

        self.assertEqual(duplicate_context.exception.detail.code, "duplicate_column_name")
        self.assertEqual(ragged_context.exception.detail.code, "ragged_csv_row")


class WorksheetRevisionTests(unittest.TestCase):
    def test_cell_edit_creates_a_new_revision_without_mutating_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.csv"
            path.write_text("value\n1\n2\n", encoding="utf-8")
            dataset = import_csv_dataset(path)

        first = create_worksheet(dataset, name="Measurements")
        second = replace_worksheet_cell(first, row_index=0, column_name="value", value=3)

        self.assertEqual(first.revision, 1)
        self.assertEqual(first.columns[0].values, (1.0, 2.0))
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.parent_digest, first.digest)
        self.assertEqual(second.columns[0].values, (3.0, 2.0))
        self.assertNotEqual(second.digest, first.digest)

    def test_cell_edit_enforces_column_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.csv"
            path.write_text("value\n1\n", encoding="utf-8")
            worksheet = create_worksheet(import_csv_dataset(path), name="Measurements")

        with self.assertRaises(AnalysisInputError) as context:
            replace_worksheet_cell(
                worksheet, row_index=0, column_name="value", value="not-a-number"
            )
        self.assertEqual(context.exception.detail.code, "invalid_column_value")

    def test_filter_sort_and_derived_column_each_create_a_new_revision(self) -> None:
        worksheet = create_worksheet(
            import_csv_bytes(b"value,divisor,part\n2,2,A\n1,1,B\n,4,A\n", location="values.csv"),
            name="Measurements",
        )
        filtered = filter_worksheet_rows(
            worksheet, column_name="part", operator="equals", value="A"
        )
        sorted_worksheet = sort_worksheet_rows(
            worksheet, column_name="value", descending=True
        )
        derived = add_derived_numeric_column(
            worksheet,
            column_name="ratio",
            source_column="value",
            operation="divide",
            operand_column="divisor",
        )

        self.assertEqual(worksheet.row_count, 3)
        self.assertEqual(filtered.revision, 2)
        self.assertEqual(filtered.columns[0].values, (2.0, None))
        self.assertEqual(filtered.transformations[-1]["operation"], "filter_rows")
        self.assertEqual(sorted_worksheet.columns[0].values, (2.0, 1.0, None))
        self.assertEqual(sorted_worksheet.columns[2].values, ("A", "B", "A"))
        self.assertEqual(derived.columns[-1].name, "ratio")
        self.assertEqual(derived.columns[-1].values, (1.0, 1.0, None))
        self.assertEqual(derived.parent_digest, worksheet.digest)

    def test_derived_column_rejects_zero_division_and_duplicate_names(self) -> None:
        worksheet = create_worksheet(
            import_csv_bytes(b"value,zero\n2,0\n", location="values.csv"), name="Measurements"
        )
        with self.assertRaises(AnalysisInputError) as zero_context:
            add_derived_numeric_column(
                worksheet,
                column_name="ratio",
                source_column="value",
                operation="divide",
                operand_column="zero",
            )
        with self.assertRaises(AnalysisInputError) as duplicate_context:
            add_derived_numeric_column(
                worksheet,
                column_name="value",
                source_column="value",
                operation="copy",
            )
        self.assertEqual(zero_context.exception.detail.code, "division_by_zero")
        self.assertEqual(duplicate_context.exception.detail.code, "duplicate_column_name")

    def test_filter_requires_a_value_except_for_missingness_checks(self) -> None:
        worksheet = create_worksheet(
            import_csv_bytes(b"value\n2\n", location="values.csv"), name="Measurements"
        )
        with self.assertRaises(AnalysisInputError) as context:
            filter_worksheet_rows(worksheet, column_name="value", operator="equals")
        self.assertEqual(context.exception.detail.code, "missing_filter_value")
