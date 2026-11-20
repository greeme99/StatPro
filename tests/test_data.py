from __future__ import annotations

import sys
import tempfile
import unittest
import hashlib
import io
import sqlite3
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.domain.data import (
    DataType,
    add_derived_numeric_column,
    create_worksheet,
    filter_worksheet_rows,
    import_csv_bytes,
    import_csv_dataset,
    inner_join_worksheet,
    import_parquet_bytes,
    import_sqlite_bytes,
    import_xlsx_bytes,
    replace_worksheet_cell,
    select_worksheet_columns,
    sort_worksheet_rows,
)
from statpro.domain.errors import AnalysisInputError


class DatasetImportTests(unittest.TestCase):
    @staticmethod
    def _parquet_bytes(table: pa.Table) -> bytes:
        stream = pa.BufferOutputStream()
        pq.write_table(table, stream)
        return stream.getvalue().to_pybytes()

    @staticmethod
    def _sqlite_bytes() -> bytes:
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute("CREATE TABLE measurements(value REAL, part TEXT, note TEXT)")
            connection.executemany(
                "INSERT INTO measurements VALUES (?, ?, ?)",
                ((10.5, "A", "ok"), (None, "B", "")),
            )
            return connection.serialize()
        finally:
            connection.close()

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

    def test_xlsx_requested_sheet_must_exist(self) -> None:
        with self.assertRaises(AnalysisInputError) as context:
            import_xlsx_bytes(self._xlsx_bytes(), location="process.xlsx", sheet_name="Missing")

        self.assertEqual(context.exception.detail.code, "xlsx_sheet_not_found")

    def test_sqlite_selected_table_preserves_source_and_nulls(self) -> None:
        source = self._sqlite_bytes()
        dataset = import_sqlite_bytes(
            source, location="process.sqlite", table_name="measurements"
        )

        columns = {column.name: column for column in dataset.columns}
        self.assertEqual(dataset.source.kind, "sqlite")
        self.assertEqual(dataset.source.location, "process.sqlite#table=measurements")
        self.assertEqual(dataset.source.content_digest, hashlib.sha256(source).hexdigest())
        self.assertEqual(dataset.row_count, 2)
        self.assertEqual(columns["value"].values, (10.5, None))
        self.assertEqual(columns["note"].values, ("ok", ""))

    def test_sqlite_rejects_unknown_table_and_blob_values(self) -> None:
        with self.assertRaises(AnalysisInputError) as missing:
            import_sqlite_bytes(
                self._sqlite_bytes(), location="process.sqlite", table_name="missing"
            )
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute("CREATE TABLE payloads(value BLOB)")
            connection.execute("INSERT INTO payloads VALUES (?)", (b"binary",))
            blob_source = connection.serialize()
        finally:
            connection.close()
        with self.assertRaises(AnalysisInputError) as blob:
            import_sqlite_bytes(
                blob_source, location="payloads.sqlite", table_name="payloads"
            )

        self.assertEqual(missing.exception.detail.code, "sqlite_table_not_found")
        self.assertEqual(blob.exception.detail.code, "sqlite_blob_not_supported")

    def test_parquet_flat_scalar_columns_preserve_types_and_nulls(self) -> None:
        source = self._parquet_bytes(pa.table({
            "value": pa.array([10.5, None], type=pa.float64()),
            "accepted": pa.array([True, False], type=pa.bool_()),
            "part": pa.array(["A", "B"], type=pa.string()),
        }))

        dataset = import_parquet_bytes(source, location="process.parquet")

        columns = {column.name: column for column in dataset.columns}
        self.assertEqual(dataset.source.kind, "parquet")
        self.assertEqual(dataset.source.location, "process.parquet")
        self.assertEqual(dataset.source.content_digest, hashlib.sha256(source).hexdigest())
        self.assertEqual(dataset.row_count, 2)
        self.assertEqual(columns["value"].values, (10.5, None))
        self.assertEqual(columns["accepted"].values, (True, False))
        self.assertEqual(columns["part"].values, ("A", "B"))

    def test_parquet_rejects_nested_columns(self) -> None:
        source = self._parquet_bytes(pa.table({"parts": pa.array([["A"], ["B"]])}))

        with self.assertRaises(AnalysisInputError) as context:
            import_parquet_bytes(source, location="nested.parquet")

        self.assertEqual(context.exception.detail.code, "parquet_type_not_supported")

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

    def test_inner_join_creates_a_left_revision_and_records_right_evidence(self) -> None:
        left = create_worksheet(
            import_csv_bytes(b"part,value\nA,10\nB,20\nA,30\n", location="left.csv"),
            name="Measurements",
        )
        right = create_worksheet(
            import_csv_bytes(b"part,operator\nA,Kim\nA,Lee\nC,Park\n", location="right.csv"),
            name="Operators",
        )

        joined = inner_join_worksheet(
            left, right_worksheet=right, left_column="part", right_column="part"
        )

        self.assertEqual(left.revision, 1)
        self.assertEqual(joined.revision, 2)
        self.assertEqual(joined.parent_digest, left.digest)
        self.assertEqual([column.name for column in joined.columns], ["part", "value", "operator"])
        self.assertEqual(joined.columns[1].values, (10.0, 10.0, 30.0, 30.0))
        self.assertEqual(joined.columns[2].values, ("Kim", "Lee", "Kim", "Lee"))
        self.assertEqual(joined.transformations[-1]["right_worksheet_digest"], right.digest)

    def test_inner_join_rejects_incompatible_keys_and_column_collisions(self) -> None:
        left = create_worksheet(import_csv_bytes(b"part,value\nA,10\n", location="left.csv"), name="Left")
        incompatible = create_worksheet(import_csv_bytes(b"part,operator\n1,Kim\n", location="right.csv"), name="Right")
        collision = create_worksheet(import_csv_bytes(b"part,value\nA,20\n", location="collision.csv"), name="Collision")

        with self.assertRaises(AnalysisInputError) as type_error:
            inner_join_worksheet(left, right_worksheet=incompatible, left_column="part", right_column="part")
        with self.assertRaises(AnalysisInputError) as collision_error:
            inner_join_worksheet(left, right_worksheet=collision, left_column="part", right_column="part")

        self.assertEqual(type_error.exception.detail.code, "incompatible_join_columns")
        self.assertEqual(collision_error.exception.detail.code, "join_column_collision")

    def test_select_columns_creates_a_revision_in_source_order_and_rejects_invalid_selection(self) -> None:
        worksheet = create_worksheet(
            import_csv_bytes(b"value,part,accepted\n10,A,true\n", location="values.csv"),
            name="Measurements",
        )

        selected = select_worksheet_columns(worksheet, column_names=["accepted", "value"])

        self.assertEqual(selected.revision, 2)
        self.assertEqual(selected.parent_digest, worksheet.digest)
        self.assertEqual([column.name for column in selected.columns], ["value", "accepted"])
        self.assertEqual(selected.transformations[-1], {"operation": "select_columns", "column_names": ["value", "accepted"]})
        with self.assertRaises(AnalysisInputError) as empty:
            select_worksheet_columns(worksheet, column_names=[])
        with self.assertRaises(AnalysisInputError) as duplicate:
            select_worksheet_columns(worksheet, column_names=["value", "value"])
        with self.assertRaises(AnalysisInputError) as unknown:
            select_worksheet_columns(worksheet, column_names=["missing"])
        self.assertEqual(empty.exception.detail.code, "empty_column_selection")
        self.assertEqual(duplicate.exception.detail.code, "duplicate_selected_column")
        self.assertEqual(unknown.exception.detail.code, "unknown_column")

    def test_filter_requires_a_value_except_for_missingness_checks(self) -> None:
        worksheet = create_worksheet(
            import_csv_bytes(b"value\n2\n", location="values.csv"), name="Measurements"
        )
        with self.assertRaises(AnalysisInputError) as context:
            filter_worksheet_rows(worksheet, column_name="value", operator="equals")
        self.assertEqual(context.exception.detail.code, "missing_filter_value")
