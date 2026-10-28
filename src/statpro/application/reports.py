"""Deterministic DOE report projection and portable export bundle."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections.abc import Mapping, Sequence
from html import escape
from typing import Any

from statpro.application.documents import DocumentStoreError, StoredDocument
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest

REPORT_TYPE = "statpro.doe.analysis_report.v1"


def build_doe_report(stored: StoredDocument) -> dict[str, Any]:
    """Project one immutable DOE Run into the versioned report contract."""

    result = _owned_doe_result(stored)
    tables = [_normalize_table(name, value) for name, value in result["tables"].items()]
    tables.sort(key=lambda table: (table["row_count"] == 0, table["name"]))
    report: dict[str, Any] = {
        "report_type": REPORT_TYPE,
        "run": {
            "run_id": stored.key,
            "storage_version": stored.storage_version,
            "etag": stored.etag,
        },
        "analysis": {
            "analysis_type": result["analysis_type"],
            "engine_version": result["engine_version"],
            "input_digest": result["input_digest"],
            "result_digest": input_digest(result),
        },
        "parameters": result["parameters"],
        "diagnostics": result["diagnostics"],
        "tables": tables,
        "plots": result["plots"],
        "assumptions": result["assumptions"],
        "warnings": result["warnings"],
        "provenance": result["provenance"],
        "limitations": [
            "Plot entries preserve result data; this export does not render chart images.",
            "This StatPro report is not a Minitab file-format or layout-equivalence claim.",
        ],
    }
    report["report_digest"] = input_digest(report)
    return report


def render_doe_report_html(report: Mapping[str, Any]) -> bytes:
    """Render the report contract as dependency-free semantic HTML."""

    run = report["run"]
    analysis = report["analysis"]
    parts = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        f"<title>StatPro DOE Report — {escape(str(run['run_id']))}</title></head><body>",
        "<main><header><h1>StatPro DOE Analysis Report</h1>",
        f"<p>Run ID: <code>{escape(str(run['run_id']))}</code></p>",
        f"<p>Analysis: {escape(str(analysis['analysis_type']))}</p>",
        f"<p>Engine: {escape(str(analysis['engine_version']))}</p>",
        f"<p>Input SHA-256: <code>{escape(str(analysis['input_digest']))}</code></p>",
        f"<p>Report SHA-256: <code>{escape(str(report['report_digest']))}</code></p></header>",
        _mapping_section("Parameters", report["parameters"]),
        _mapping_section("Diagnostics", report["diagnostics"]),
        _mapping_section("Plot data", report["plots"]),
    ]
    for table in report["tables"]:
        parts.append(_html_table(table))
    for title, key in (
        ("Warnings", "warnings"),
        ("Assumptions", "assumptions"),
        ("Limitations", "limitations"),
    ):
        items = report[key]
        parts.append(
            f"<section><h2>{title}</h2><ul>"
            + "".join(f"<li>{escape(str(item))}</li>" for item in items)
            + "</ul></section>"
        )
    parts.append("<section><h2>Provenance</h2><ul>")
    for source in report["provenance"]:
        parts.append(
            f"<li><a href=\"{escape(str(source['url']), quote=True)}\">"
            f"{escape(str(source['title']))}</a> ({escape(str(source['authority']))})</li>"
        )
    parts.append("</ul></section></main></body></html>")
    return "".join(parts).encode("utf-8")


def export_doe_report_zip(report: Mapping[str, Any]) -> bytes:
    """Return a deterministic ZIP containing HTML, JSON, and one CSV per table."""

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_zip_entry(archive, "report.html", render_doe_report_html(report))
        _write_zip_entry(
            archive,
            "report.json",
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"),
        )
        for index, table in enumerate(report["tables"], start=1):
            if not table["columns"]:
                continue
            name = _safe_name(str(table["name"]))
            _write_zip_entry(
                archive,
                f"tables/{index:02d}-{name}.csv",
                _table_csv(table),
            )
    return output.getvalue()


def _owned_doe_result(stored: StoredDocument) -> dict[str, Any]:
    document = stored.document
    result = document.get("result")
    if (
        stored.collection != "analysis-runs"
        or document.get("kind") != "analysis_run"
        or document.get("run_id") != stored.key
        or not isinstance(result, dict)
    ):
        raise DocumentStoreError("Stored analysis Run does not match its owned format.")
    required = {
        "analysis_type": str,
        "engine_version": str,
        "input_digest": str,
        "parameters": dict,
        "tables": dict,
        "plots": dict,
        "diagnostics": dict,
        "assumptions": list,
        "warnings": list,
        "provenance": list,
    }
    if any(not isinstance(result.get(key), expected) for key, expected in required.items()):
        raise DocumentStoreError("Stored analysis Run has an invalid ResultBundle.")
    if not result["analysis_type"].startswith("doe."):
        raise AnalysisInputError(
            "unsupported_report_type",
            "The DOE report endpoint requires a DOE analysis Run.",
            "run_id",
        )
    return result


def _normalize_table(name: str, value: object) -> dict[str, Any]:
    if isinstance(value, list):
        source_rows: Sequence[object] = value
    else:
        source_rows = [value]
    rows = [row if isinstance(row, dict) else {"value": row} for row in source_rows]
    columns = list(dict.fromkeys(key for row in rows for key in row))
    return {"name": name, "columns": columns, "row_count": len(rows), "rows": rows}


def _mapping_section(title: str, values: Mapping[str, object]) -> str:
    rows = "".join(
        f"<tr><th scope=\"row\">{escape(str(key))}</th><td>{escape(_cell(value))}</td></tr>"
        for key, value in sorted(values.items())
    )
    return f"<section><h2>{title}</h2><table><tbody>{rows}</tbody></table></section>"


def _html_table(table: Mapping[str, Any]) -> str:
    columns = table["columns"]
    head = "".join(f"<th scope=\"col\">{escape(str(column))}</th>" for column in columns)
    body = "".join(
        "<tr>"
        + "".join(f"<td>{escape(_cell(row.get(column)))}</td>" for column in columns)
        + "</tr>"
        for row in table["rows"]
    )
    return (
        f"<section><h2>{escape(str(table['name']))}</h2>"
        f"<p>{table['row_count']} row(s)</p><table><thead><tr>{head}</tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


def _table_csv(table: Mapping[str, Any]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=table["columns"], lineterminator="\n")
    writer.writeheader()
    for row in table["rows"]:
        writer.writerow({column: _cell(row.get(column)) for column in table["columns"]})
    return stream.getvalue().encode("utf-8-sig")


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.") or "table"


def _write_zip_entry(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = zipfile.ZIP_DEFLATED
    entry.external_attr = 0o600 << 16
    archive.writestr(entry, content)
