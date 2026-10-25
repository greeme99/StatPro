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
