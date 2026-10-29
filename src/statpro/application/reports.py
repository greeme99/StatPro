"""Deterministic DOE report projection and portable export bundle."""

from __future__ import annotations

import base64
import csv
import io
import json
import math
import re
import zipfile
from collections.abc import Mapping, Sequence
from html import escape
from typing import Any

from statpro.application.documents import DocumentStoreError, StoredDocument
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest

REPORT_TYPE = "statpro.doe.analysis_report.v2"
REPORT_TEMPLATE_IDS = ("standard", "customer_review", "regulatory_review")


def build_doe_report(
    stored: StoredDocument, *, template_id: str = "standard"
) -> dict[str, Any]:
    """Project one immutable DOE Run into the versioned report contract."""

    result = _owned_doe_result(stored)
    template = _report_template(template_id)
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
        "figures": _figure_manifest(result["plots"]),
        "template": template,
        "assumptions": result["assumptions"],
        "warnings": result["warnings"],
        "provenance": result["provenance"],
        "limitations": [
            "SVG figures are rendered only from the stored ResultBundle plot data; unsupported plot shapes remain available as data only.",
            "Customer and regulatory review templates are a structured starting point, not a customer acceptance or regulatory compliance claim.",
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
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">",
        f"<title>StatPro DOE 보고서 — {escape(str(run['run_id']))}</title></head><body>",
        "<main><header><h1>StatPro 실험계획법(DOE) 분석 보고서</h1>",
        f"<p>보고서 양식: {escape(str(report['template']['name']))}</p>",
        f"<p>분석 실행 ID: <code>{escape(str(run['run_id']))}</code></p>",
        f"<p>분석: {escape(str(analysis['analysis_type']))}</p>",
        f"<p>엔진: {escape(str(analysis['engine_version']))}</p>",
        f"<p>입력 SHA-256: <code>{escape(str(analysis['input_digest']))}</code></p>",
        f"<p>보고서 SHA-256: <code>{escape(str(report['report_digest']))}</code></p></header>",
        _template_section(report["template"]),
        _mapping_section("파라미터", report["parameters"]),
        _mapping_section("진단", report["diagnostics"]),
        _figure_section(report),
        _mapping_section("Plot 데이터", report["plots"]),
    ]
    for table in report["tables"]:
        parts.append(_html_table(table))
    for title, key in (
        ("경고", "warnings"),
        ("가정", "assumptions"),
        ("제한 사항", "limitations"),
    ):
        items = report[key]
        parts.append(
            f"<section><h2>{title}</h2><ul>"
            + "".join(f"<li>{escape(str(item))}</li>" for item in items)
            + "</ul></section>"
        )
    parts.append("<section><h2>근거 출처</h2><ul>")
    for source in report["provenance"]:
        parts.append(
            f"<li><a href=\"{escape(str(source['url']), quote=True)}\">"
            f"{escape(str(source['title']))}</a> ({escape(str(source['authority']))})</li>"
        )
    parts.append("</ul></section></main></body></html>")
    return "".join(parts).encode("utf-8")


def render_doe_report_figures(report: Mapping[str, Any]) -> dict[str, bytes]:
    """Render deterministic SVG figures from supported, already-owned DOE plot data."""

    figures: dict[str, bytes] = {}
    for figure in report["figures"]:
        source = report["plots"].get(figure["source_plot"])
        if not isinstance(source, Mapping):
            continue
        rendered = _render_figure(figure, source)
        if rendered is not None:
            figures[figure["file_name"]] = rendered
    return figures


def export_doe_report_zip(report: Mapping[str, Any]) -> bytes:
    """Return a deterministic ZIP containing HTML, JSON, SVG figures, and CSV tables."""

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_zip_entry(archive, "report.html", render_doe_report_html(report))
        _write_zip_entry(
            archive,
            "report.json",
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"),
        )
        for name, figure in render_doe_report_figures(report).items():
            _write_zip_entry(archive, name, figure)
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


def _report_template(template_id: str) -> dict[str, Any]:
    templates = {
        "standard": {
            "id": "standard",
            "name": "표준 분석 보고서",
            "intended_use": "분석 실행의 결과, 근거 및 제한 사항을 검토합니다.",
            "review_fields": [],
        },
        "customer_review": {
            "id": "customer_review",
            "name": "고객 검토용 보고서",
            "intended_use": "고객 요구사항과 검토 이력을 연결하기 위한 검토용 양식입니다.",
            "review_fields": ["고객명", "요구사항 또는 계약 ID", "검토 책임자", "검토 일자"],
        },
        "regulatory_review": {
            "id": "regulatory_review",
            "name": "규제 검토용 보고서",
            "intended_use": "조직이 적용 규정과 제출 요건을 대조하기 위한 검토용 양식입니다.",
            "review_fields": ["적용 규정 또는 표준", "적용 범위", "검토 책임자", "승인 또는 제출 상태"],
        },
    }
    try:
        return templates[template_id]
    except KeyError as error:
        raise AnalysisInputError(
            "unsupported_report_template",
            "The requested DOE report template is not supported.",
            "template_id",
        ) from error


def _figure_manifest(plots: Mapping[str, object]) -> list[dict[str, str]]:
    figures: list[dict[str, str]] = []
    for plot_name, plot in sorted(plots.items()):
        if not isinstance(plot, Mapping):
            continue
        if _bar_plot_values(plot) is not None:
            kind = "bar"
            title = f"{plot_name} 막대 그래프"
        elif _series_plot_values(plot) is not None:
            kind = "series"
            title = f"{plot_name} 선 그래프"
        else:
            continue
        safe_name = _safe_name(str(plot_name))
        figures.append(
            {
                "id": safe_name,
                "source_plot": str(plot_name),
                "kind": kind,
                "title": title,
                "alt": f"{title}. 원본 수치는 보고서의 Plot 데이터와 표를 참조하십시오.",
                "file_name": f"charts/{safe_name}.svg",
            }
        )
    return figures


def _template_section(template: Mapping[str, object]) -> str:
    fields = template.get("review_fields", [])
    if not isinstance(fields, list) or not fields:
        return ""
    items = "".join(
        f"<li>{escape(str(field))}: <strong>조직 입력 필요</strong></li>" for field in fields
    )
    return (
        "<section><h2>검토 준비 항목</h2>"
        f"<p>{escape(str(template['intended_use']))}</p><ul>{items}</ul>"
        "<p>이 양식은 규제 준수 또는 고객 승인 여부를 판정하지 않습니다.</p></section>"
    )


def _figure_section(report: Mapping[str, Any]) -> str:
    figures = render_doe_report_figures(report)
    if not figures:
        return "<section><h2>그래프 이미지</h2><p>이 분석 실행에는 SVG로 렌더링할 수 있는 Plot 데이터가 없습니다.</p></section>"
    parts = ["<section><h2>그래프 이미지</h2>"]
    for figure in report["figures"]:
        content = figures.get(figure["file_name"])
        if content is None:
            continue
        encoded = base64.b64encode(content).decode("ascii")
        parts.append(
            f"<figure><figcaption>{escape(str(figure['title']))}</figcaption>"
            f"<img src=\"data:image/svg+xml;base64,{encoded}\" alt=\"{escape(str(figure['alt']), quote=True)}\">"
            "</figure>"
        )
    return "".join(parts) + "</section>"


def _render_figure(figure: Mapping[str, str], plot: Mapping[str, object]) -> bytes | None:
    if figure["kind"] == "bar":
        values = _bar_plot_values(plot)
        if values is not None:
            return _bar_svg(figure, *values)
    if figure["kind"] == "series":
        values = _series_plot_values(plot)
        if values is not None:
            return _series_svg(figure, *values)
    return None


def _bar_plot_values(plot: Mapping[str, object]) -> tuple[list[str], list[float], float | None] | None:
    terms = plot.get("terms")
    if not isinstance(terms, list):
        return None
    values = next((plot.get(key) for key in ("display_values", "values", "effects") if key in plot), None)
    numeric = _numeric_values(values)
    if numeric is None or len(terms) != len(numeric) or not terms:
        return None
    reference = plot.get("reference_line")
    return [str(term) for term in terms], numeric, _finite_number(reference)


def _series_plot_values(plot: Mapping[str, object]) -> tuple[list[float], list[float]] | None:
    candidates = (
        ("run_order", "residuals"),
        ("fitted", "residuals"),
        ("x", "y"),
    )
    for x_key, y_key in candidates:
        x_values = _numeric_values(plot.get(x_key))
        y_values = _numeric_values(plot.get(y_key))
        if x_values and y_values and len(x_values) == len(y_values):
            return x_values, y_values
    return None


def _numeric_values(value: object) -> list[float] | None:
    if not isinstance(value, list):
        return None
    numbers = [_finite_number(item) for item in value]
    if any(number is None for number in numbers):
        return None
    return [number for number in numbers if number is not None]


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _svg_document(title: str, description: str, body: str) -> bytes:
    return (
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"960\" height=\"540\" viewBox=\"0 0 960 540\" role=\"img\" aria-labelledby=\"title desc\">"
        f"<title id=\"title\">{escape(title)}</title><desc id=\"desc\">{escape(description)}</desc>"
        "<rect width=\"960\" height=\"540\" fill=\"#ffffff\"/><rect x=\"96\" y=\"56\" width=\"816\" height=\"392\" fill=\"#ffffff\" stroke=\"#aab4c2\"/>"
        f"{body}</svg>"
    ).encode()


def _bar_svg(
    figure: Mapping[str, str], terms: list[str], values: list[float], reference: float | None
) -> bytes:
    minimum = min(0.0, *values, *( [reference] if reference is not None else []))
    maximum = max(0.0, *values, *( [reference] if reference is not None else []))
    scale = maximum - minimum or 1.0
    x_width = 816 / len(values)
    y_at = lambda value: 448 - ((value - minimum) / scale * 392)
    zero = y_at(0.0)
    bars = []
    labels = []
    for index, (term, value) in enumerate(zip(terms, values, strict=True)):
        left = 96 + index * x_width + x_width * 0.15
        width = x_width * 0.7
        top = min(y_at(value), zero)
        height = abs(y_at(value) - zero)
        bars.append(f"<rect x=\"{left:.3f}\" y=\"{top:.3f}\" width=\"{width:.3f}\" height=\"{max(height, 1):.3f}\" fill=\"#1769c2\"/>")
        labels.append(f"<text x=\"{left + width / 2:.3f}\" y=\"474\" text-anchor=\"middle\" font-family=\"sans-serif\" font-size=\"12\" fill=\"#1f2937\">{escape(term)}</text>")
    reference_line = ""
    if reference is not None:
        reference_line = f"<line x1=\"96\" y1=\"{y_at(reference):.3f}\" x2=\"912\" y2=\"{y_at(reference):.3f}\" stroke=\"#c62828\" stroke-dasharray=\"8 6\"/>"
    body = (
        f"<line x1=\"96\" y1=\"{zero:.3f}\" x2=\"912\" y2=\"{zero:.3f}\" stroke=\"#536171\"/>"
        f"<text x=\"96\" y=\"34\" font-family=\"sans-serif\" font-size=\"18\" font-weight=\"700\" fill=\"#17212f\">{escape(figure['title'])}</text>"
        f"{reference_line}{''.join(bars)}{''.join(labels)}"
    )
    return _svg_document(figure["title"], figure["alt"], body)


def _series_svg(figure: Mapping[str, str], x_values: list[float], y_values: list[float]) -> bytes:
    minimum = min(y_values)
    maximum = max(y_values)
    span = maximum - minimum or 1.0
    min_x = min(x_values)
    max_x = max(x_values)
    x_span = max_x - min_x or 1.0
    points = []
    circles = []
    for x_value, y_value in zip(x_values, y_values, strict=True):
        x = 96 + (x_value - min_x) / x_span * 816
        y = 448 - (y_value - minimum) / span * 392
        points.append(f"{x:.3f},{y:.3f}")
        circles.append(f"<circle cx=\"{x:.3f}\" cy=\"{y:.3f}\" r=\"4\" fill=\"#1769c2\"/>")
    body = (
        f"<text x=\"96\" y=\"34\" font-family=\"sans-serif\" font-size=\"18\" font-weight=\"700\" fill=\"#17212f\">{escape(figure['title'])}</text>"
        "<line x1=\"96\" y1=\"448\" x2=\"912\" y2=\"448\" stroke=\"#536171\"/>"
        f"<polyline points=\"{' '.join(points)}\" fill=\"none\" stroke=\"#1769c2\" stroke-width=\"3\"/>{''.join(circles)}"
    )
    return _svg_document(figure["title"], figure["alt"], body)


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
