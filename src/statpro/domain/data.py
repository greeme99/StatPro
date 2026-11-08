"""Immutable Dataset and Worksheet snapshot contracts."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest

CellValue = float | bool | str | None


class DataType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    LOGICAL = "logical"


@dataclass(frozen=True, slots=True)
class DatasetSource:
    kind: str
    location: str
    media_type: str
    content_digest: str


@dataclass(frozen=True, slots=True)
class DataColumn:
    name: str
    data_type: DataType
    values: tuple[CellValue, ...]

    @property
    def missing_count(self) -> int:
        return sum(value is None for value in self.values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "nullable": self.missing_count > 0,
            "missing_count": self.missing_count,
            "values": list(self.values),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DataColumn:
        return cls(
            name=payload["name"],
            data_type=DataType(payload["data_type"]),
            values=tuple(payload["values"]),
        )


@dataclass(frozen=True, slots=True)
class DatasetSnapshot:
    dataset_id: str
    digest: str
    source: DatasetSource
    columns: tuple[DataColumn, ...]
    row_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "digest": self.digest,
            "source": {
                "kind": self.source.kind,
                "location": self.source.location,
                "media_type": self.source.media_type,
                "content_digest": self.source.content_digest,
            },
            "row_count": self.row_count,
            "column_count": len(self.columns),
            "columns": [column.to_dict() for column in self.columns],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DatasetSnapshot:
        source = payload["source"]
        return cls(
            dataset_id=payload["dataset_id"],
            digest=payload["digest"],
            source=DatasetSource(
                kind=source["kind"],
                location=source["location"],
                media_type=source["media_type"],
                content_digest=source["content_digest"],
            ),
            columns=tuple(DataColumn.from_dict(column) for column in payload["columns"]),
            row_count=payload["row_count"],
        )


@dataclass(frozen=True, slots=True)
class WorksheetSnapshot:
    worksheet_id: str
    name: str
    base_dataset_digest: str
    digest: str
    revision: int
    parent_digest: str | None
    columns: tuple[DataColumn, ...]
    transformations: tuple[dict[str, Any], ...] = ()

    @property
    def row_count(self) -> int:
        return len(self.columns[0].values) if self.columns else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "worksheet_id": self.worksheet_id,
            "name": self.name,
            "base_dataset_digest": self.base_dataset_digest,
            "digest": self.digest,
            "revision": self.revision,
            "parent_digest": self.parent_digest,
            "row_count": self.row_count,
            "columns": [column.to_dict() for column in self.columns],
            "transformations": list(self.transformations),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorksheetSnapshot:
        return cls(
            worksheet_id=payload["worksheet_id"],
            name=payload["name"],
            base_dataset_digest=payload["base_dataset_digest"],
            digest=payload["digest"],
            revision=payload["revision"],
            parent_digest=payload["parent_digest"],
            columns=tuple(DataColumn.from_dict(column) for column in payload["columns"]),
            transformations=tuple(payload["transformations"]),
        )


def _parse_value(value: str, data_type: DataType, field: str) -> CellValue:
    if data_type == DataType.NUMERIC:
        try:
            numeric = float(value)
        except ValueError as error:
            raise AnalysisInputError(
                "invalid_column_value", f"'{value}' is not numeric.", field
            ) from error
        if not math.isfinite(numeric):
            raise AnalysisInputError("non_finite_value", "Numeric values must be finite.", field)
        return numeric
    if data_type == DataType.LOGICAL:
        normalized = value.casefold()
        if normalized not in {"true", "false"}:
            raise AnalysisInputError(
                "invalid_column_value", f"'{value}' is not true or false.", field
            )
        return normalized == "true"
    if data_type == DataType.DATETIME:
        try:
            return datetime.fromisoformat(value).isoformat()
        except ValueError as error:
            raise AnalysisInputError(
                "invalid_column_value", f"'{value}' is not an ISO 8601 date-time.", field
            ) from error
    return value


def _infer_type(values: Sequence[str]) -> DataType:
    if values and all(value.casefold() in {"true", "false"} for value in values):
        return DataType.LOGICAL
    try:
        for value in values:
            numeric = float(value)
            if not math.isfinite(numeric):
                return DataType.TEXT
        if values:
            return DataType.NUMERIC
    except ValueError:
        pass
    try:
        for value in values:
            datetime.fromisoformat(value)
        if values:
            return DataType.DATETIME
    except ValueError:
        pass
    return DataType.TEXT


def import_csv_dataset(
    path: Path,
    *,
    type_hints: Mapping[str, DataType] | None = None,
    missing_tokens: Sequence[str] = ("",),
    encoding: str = "utf-8-sig",
) -> DatasetSnapshot:
    """Import a bounded CSV file as an immutable, content-addressed Dataset."""

    try:
        source_bytes = path.read_bytes()
    except OSError as error:
        raise AnalysisInputError("csv_read_failed", str(error), "path") from error

    return import_csv_bytes(
        source_bytes,
        location=str(path.resolve()),
        type_hints=type_hints,
        missing_tokens=missing_tokens,
        encoding=encoding,
        error_field="path",
    )


def import_csv_bytes(
    source_bytes: bytes,
    *,
    location: str,
    type_hints: Mapping[str, DataType] | None = None,
    missing_tokens: Sequence[str] = ("",),
    encoding: str = "utf-8-sig",
    error_field: str = "content",
) -> DatasetSnapshot:
    """Import caller-owned CSV bytes without requiring a temporary filesystem path."""

    try:
        text = source_bytes.decode(encoding)
    except UnicodeError as error:
        raise AnalysisInputError("csv_read_failed", str(error), error_field) from error

    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows or not rows[0]:
        raise AnalysisInputError("empty_csv", "CSV input requires a header row.", error_field)
    headers = [header.strip() for header in rows[0]]
    if any(not header for header in headers):
        raise AnalysisInputError("empty_column_name", "Every CSV column needs a name.", "header")
    if len(set(headers)) != len(headers):
        raise AnalysisInputError("duplicate_column_name", "CSV column names must be unique.", "header")
    data_rows = rows[1:]
    if len(data_rows) > 1_000_000:
        raise AnalysisInputError(
            "dataset_too_large", "CSV import supports at most 1,000,000 rows.", error_field
        )
    for row_index, row in enumerate(data_rows, start=2):
        if len(row) != len(headers):
            raise AnalysisInputError(
                "ragged_csv_row",
                f"CSV row {row_index} has {len(row)} values; expected {len(headers)}.",
                f"row[{row_index}]",
            )

    hints = dict(type_hints or {})
    unknown_hints = sorted(set(hints) - set(headers))
    if unknown_hints:
        raise AnalysisInputError(
            "unknown_type_hint",
            f"Type hints reference unknown columns: {', '.join(unknown_hints)}.",
            "type_hints",
        )
    missing = set(missing_tokens)
    columns: list[DataColumn] = []
    for column_index, name in enumerate(headers):
        raw_values = [row[column_index] for row in data_rows]
        observed = [value for value in raw_values if value not in missing]
        data_type = hints.get(name, _infer_type(observed))
        parsed = tuple(
            None
            if value in missing
            else _parse_value(value, data_type, f"columns[{name}][{row_index}]")
            for row_index, value in enumerate(raw_values)
        )
        columns.append(DataColumn(name=name, data_type=data_type, values=parsed))

    normalized_payload = {
        "columns": [column.to_dict() for column in columns],
        "missing_tokens": list(missing_tokens),
        "encoding": encoding,
    }
    digest = input_digest(normalized_payload)
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    return DatasetSnapshot(
        dataset_id=f"ds_{digest[:16]}",
        digest=digest,
        source=DatasetSource(
            kind="csv",
            location=location,
            media_type="text/csv",
            content_digest=source_digest,
        ),
        columns=tuple(columns),
        row_count=len(data_rows),
    )


def create_worksheet(dataset: DatasetSnapshot, *, name: str) -> WorksheetSnapshot:
    normalized_name = name.strip()
    if not normalized_name:
        raise AnalysisInputError("empty_worksheet_name", "Worksheet needs a name.", "name")
    payload = {
        "name": normalized_name,
        "base_dataset_digest": dataset.digest,
        "revision": 1,
        "columns": [column.to_dict() for column in dataset.columns],
        "transformations": [],
    }
    digest = input_digest(payload)
    return WorksheetSnapshot(
        worksheet_id=f"ws_{digest[:16]}",
        name=normalized_name,
        base_dataset_digest=dataset.digest,
        digest=digest,
        revision=1,
        parent_digest=None,
        columns=dataset.columns,
    )


def replace_worksheet_cell(
    worksheet: WorksheetSnapshot, *, row_index: int, column_name: str, value: CellValue
) -> WorksheetSnapshot:
    if isinstance(row_index, bool) or not isinstance(row_index, int):
        raise AnalysisInputError("invalid_row_index", "Row index must be an integer.", "row_index")
    if row_index < 0 or row_index >= worksheet.row_count:
        raise AnalysisInputError("row_out_of_range", "Row index is outside the worksheet.", "row_index")
    column_positions = {column.name: index for index, column in enumerate(worksheet.columns)}
    if column_name not in column_positions:
        raise AnalysisInputError(
            "unknown_column", f"Worksheet has no column named '{column_name}'.", "column_name"
        )
    position = column_positions[column_name]
    column = worksheet.columns[position]
    normalized_value = (
        None
        if value is None
        else _parse_value(str(value), column.data_type, f"columns[{column_name}][{row_index}]")
    )
    values = list(column.values)
    values[row_index] = normalized_value
    columns = list(worksheet.columns)
    columns[position] = replace(column, values=tuple(values))
    transformation = {
        "operation": "replace_cell",
        "row_index": row_index,
        "column_name": column_name,
        "value": normalized_value,
    }
    transformations = worksheet.transformations + (transformation,)
    revision = worksheet.revision + 1
    payload = {
        "name": worksheet.name,
        "base_dataset_digest": worksheet.base_dataset_digest,
        "revision": revision,
        "parent_digest": worksheet.digest,
        "columns": [item.to_dict() for item in columns],
        "transformations": list(transformations),
    }
    digest = input_digest(payload)
    return WorksheetSnapshot(
        worksheet_id=worksheet.worksheet_id,
        name=worksheet.name,
        base_dataset_digest=worksheet.base_dataset_digest,
        digest=digest,
        revision=revision,
        parent_digest=worksheet.digest,
        columns=tuple(columns),
        transformations=transformations,
    )


def _revise_worksheet(
    worksheet: WorksheetSnapshot,
    *,
    columns: tuple[DataColumn, ...],
    transformation: dict[str, Any],
) -> WorksheetSnapshot:
    """Create the single next immutable Worksheet revision for a transformation."""

    transformations = worksheet.transformations + (transformation,)
    revision = worksheet.revision + 1
    payload = {
        "name": worksheet.name,
        "base_dataset_digest": worksheet.base_dataset_digest,
        "revision": revision,
        "parent_digest": worksheet.digest,
        "columns": [item.to_dict() for item in columns],
        "transformations": list(transformations),
    }
    digest = input_digest(payload)
    return WorksheetSnapshot(
        worksheet_id=worksheet.worksheet_id,
        name=worksheet.name,
        base_dataset_digest=worksheet.base_dataset_digest,
        digest=digest,
        revision=revision,
        parent_digest=worksheet.digest,
        columns=columns,
        transformations=transformations,
    )


def _worksheet_column(worksheet: WorksheetSnapshot, column_name: str) -> DataColumn:
    for column in worksheet.columns:
        if column.name == column_name:
            return column
    raise AnalysisInputError(
        "unknown_column", f"Worksheet has no column named '{column_name}'.", "column_name"
    )


def filter_worksheet_rows(
    worksheet: WorksheetSnapshot,
    *,
    column_name: str,
    operator: str,
    value: CellValue = None,
) -> WorksheetSnapshot:
    """Keep rows matching a typed, auditable filter as a new Worksheet revision."""

    column = _worksheet_column(worksheet, column_name)
    allowed = {
        "equals",
        "not_equals",
        "greater_than",
        "greater_or_equal",
        "less_than",
        "less_or_equal",
        "contains",
        "is_missing",
        "is_not_missing",
    }
    if operator not in allowed:
        raise AnalysisInputError("invalid_filter_operator", "Unsupported worksheet filter.", "operator")
    if operator in {"greater_than", "greater_or_equal", "less_than", "less_or_equal"} and column.data_type != DataType.NUMERIC:
        raise AnalysisInputError("invalid_filter_type", "Numeric comparisons require a numeric column.", "column_name")
    if operator == "contains" and column.data_type not in {DataType.TEXT, DataType.CATEGORICAL}:
        raise AnalysisInputError("invalid_filter_type", "Contains requires a text or categorical column.", "column_name")
    if operator not in {"is_missing", "is_not_missing"} and value is None:
        raise AnalysisInputError("missing_filter_value", "This filter requires a comparison value.", "value")
    if operator not in {"is_missing", "is_not_missing"} and value is not None:
        normalized_value = _parse_value(str(value), column.data_type, "value")
    else:
        normalized_value = value

    def matches(observed: CellValue) -> bool:
        if operator == "is_missing":
            return observed is None
        if operator == "is_not_missing":
            return observed is not None
        if observed is None:
            return False
        if operator == "equals":
            return observed == normalized_value
        if operator == "not_equals":
            return observed != normalized_value
        if operator == "contains":
            return str(normalized_value).casefold() in str(observed).casefold()
        if operator == "greater_than":
            return observed > normalized_value  # type: ignore[operator]
        if operator == "greater_or_equal":
            return observed >= normalized_value  # type: ignore[operator]
        if operator == "less_than":
            return observed < normalized_value  # type: ignore[operator]
        return observed <= normalized_value  # type: ignore[operator]

    row_indexes = tuple(index for index, observed in enumerate(column.values) if matches(observed))
    columns = tuple(
        replace(item, values=tuple(item.values[index] for index in row_indexes))
        for item in worksheet.columns
    )
    return _revise_worksheet(
        worksheet,
        columns=columns,
        transformation={
            "operation": "filter_rows",
            "column_name": column_name,
            "operator": operator,
            "value": normalized_value,
            "kept_row_count": len(row_indexes),
        },
    )


def sort_worksheet_rows(
    worksheet: WorksheetSnapshot, *, column_name: str, descending: bool = False
) -> WorksheetSnapshot:
    """Stable-sort nonmissing rows while retaining missing values at the end."""

    column = _worksheet_column(worksheet, column_name)
    sortable_types = {DataType.NUMERIC, DataType.TEXT, DataType.CATEGORICAL, DataType.DATETIME, DataType.LOGICAL}
    if column.data_type not in sortable_types:
        raise AnalysisInputError("invalid_sort_type", "Column type cannot be sorted.", "column_name")
    present = [index for index, value in enumerate(column.values) if value is not None]
    missing = [index for index, value in enumerate(column.values) if value is None]
    present.sort(key=lambda index: column.values[index], reverse=descending)
    row_indexes = tuple(present + missing)
    columns = tuple(
        replace(item, values=tuple(item.values[index] for index in row_indexes))
        for item in worksheet.columns
    )
    return _revise_worksheet(
        worksheet,
        columns=columns,
        transformation={
            "operation": "sort_rows",
            "column_name": column_name,
            "descending": descending,
            "missing_position": "last",
        },
    )


def add_derived_numeric_column(
    worksheet: WorksheetSnapshot,
    *,
    column_name: str,
    source_column: str,
    operation: str,
    operand_column: str | None = None,
    operand_constant: float | None = None,
) -> WorksheetSnapshot:
    """Append a numeric arithmetic column without evaluating arbitrary expressions."""

    normalized_name = column_name.strip()
    if not normalized_name:
        raise AnalysisInputError("empty_column_name", "Derived column needs a name.", "column_name")
    if any(column.name == normalized_name for column in worksheet.columns):
        raise AnalysisInputError("duplicate_column_name", "Worksheet column names must be unique.", "column_name")
    source = _worksheet_column(worksheet, source_column)
    if source.data_type != DataType.NUMERIC:
        raise AnalysisInputError("invalid_derived_source", "Derived arithmetic requires a numeric source column.", "source_column")
    allowed = {"copy", "add", "subtract", "multiply", "divide"}
    if operation not in allowed:
        raise AnalysisInputError("invalid_derived_operation", "Unsupported derived column operation.", "operation")
    if operation == "copy" and (operand_column is not None or operand_constant is not None):
        raise AnalysisInputError("unexpected_derived_operand", "Copy does not use an operand.", "operation")
    if operation != "copy" and ((operand_column is None) == (operand_constant is None)):
        raise AnalysisInputError("invalid_derived_operand", "Use exactly one operand column or numeric constant.", "operand")
    if operand_column is not None:
        operand = _worksheet_column(worksheet, operand_column)
        if operand.data_type != DataType.NUMERIC:
            raise AnalysisInputError("invalid_derived_operand", "Operand column must be numeric.", "operand_column")
        operand_values = operand.values
    else:
        if operand_constant is not None and (isinstance(operand_constant, bool) or not math.isfinite(operand_constant)):
            raise AnalysisInputError("invalid_derived_operand", "Operand constant must be finite.", "operand_constant")
        operand_values = tuple(operand_constant for _ in range(worksheet.row_count))
    values: list[CellValue] = []
    for row_index, source_value in enumerate(source.values):
        operand_value = operand_values[row_index]
        if source_value is None or operand_value is None:
            values.append(None)
            continue
        left = float(source_value)
        right = float(operand_value)
        if operation == "copy":
            values.append(left)
        elif operation == "add":
            values.append(left + right)
        elif operation == "subtract":
            values.append(left - right)
        elif operation == "multiply":
            values.append(left * right)
        else:
            if right == 0:
                raise AnalysisInputError("division_by_zero", "Derived column cannot divide by zero.", f"operand[{row_index}]")
            values.append(left / right)
    new_column = DataColumn(name=normalized_name, data_type=DataType.NUMERIC, values=tuple(values))
    return _revise_worksheet(
        worksheet,
        columns=worksheet.columns + (new_column,),
        transformation={
            "operation": "add_derived_numeric_column",
            "column_name": normalized_name,
            "source_column": source_column,
            "arithmetic": operation,
            "operand_column": operand_column,
            "operand_constant": operand_constant,
        },
    )
