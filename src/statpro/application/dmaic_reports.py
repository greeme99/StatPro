"""Immutable DMAIC project report projections and portable document renderers."""

from __future__ import annotations

import io
from collections.abc import Mapping
from typing import Any

from statpro.domain.identity import input_digest


def build_dmaic_report(
    *, project: Mapping[str, Any], storage_version: int, etag: str
) -> dict[str, Any]:
    """Project the stored revision and linked evidence identities into one report."""

    references = _evidence_references(project)
    report: dict[str, Any] = {
        "report_type": "statpro.dmaic.project_report.v1",
        "project": project,
        "project_revision": int(project["revision"]),
        "storage_version": storage_version,
        "etag": etag,
        "evidence_references": references,
        "limitations": [
            "The report records referenced analysis identities; it does not re-run analyses.",
            "A document export is a review artifact and does not constitute approval or execution.",
        ],
    }
    report["report_digest"] = input_digest(report)
    return report


def render_dmaic_report_docx(report: Mapping[str, Any]) -> bytes:
    """Create a Word review document with project revision and evidence linkage."""

    try:
        from docx import Document
        from docx.shared import Inches
    except ImportError as error:  # pragma: no cover - installation boundary
        raise RuntimeError("Install StatPro with the 'advanced' extra for Word export.") from error

    project = report["project"]
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    title = document.add_paragraph(style="Title")
    title.add_run("DMAIC Project Review Report")
    document.add_paragraph(
        f"{project['title']} project revision {report['project_revision']} is recorded with its linked analysis evidence and document revisions."
    )
    document.add_heading("Project identity", level=1)
    _add_key_value_table(document, {
        "Project ID": project["project_id"], "Owner": project["owner_ref"],
        "Status": project["status"], "Project digest": project["digest"],
        "Report digest": report["report_digest"],
    })
    document.add_heading("DMAIC document revisions", level=1)
    references = _document_revisions(project)
    _add_rows_table(document, ["Phase document", "Document ID", "Revision", "Digest"], references)
    document.add_heading("Analysis evidence references", level=1)
    _add_rows_table(document, ["Path", "Run ID", "ETag or digest"], report["evidence_references"])
    document.add_heading("Review limitations", level=1)
    for item in report["limitations"]:
        document.add_paragraph(str(item), style="List Bullet")
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def _document_revisions(project: Mapping[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for name, value in project.items():
        if not isinstance(value, Mapping) or "document_id" not in value:
            continue
        rows.append([name, str(value.get("document_id", "")), str(value.get("revision", "")), str(value.get("digest", ""))])
    return rows or [["No saved phase documents", "", "", ""]]


def _evidence_references(value: object, path: str = "project") -> list[list[str]]:
    found: list[list[str]] = []
    if isinstance(value, Mapping):
        run_id = value.get("run_id")
        if isinstance(run_id, str):
            found.append([path, run_id, str(value.get("run_etag", value.get("run_digest", "")))])
        for key, child in value.items():
            found.extend(_evidence_references(child, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_evidence_references(child, f"{path}[{index}]") )
    return found


def _add_key_value_table(document: Any, values: Mapping[str, object]) -> None:
    _add_rows_table(document, ["Field", "Value"], [[key, str(value)] for key, value in values.items()])


def _add_rows_table(document: Any, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, value in zip(table.rows[0].cells, headers, strict=True):
        cell.text = value
    for values in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, values, strict=True):
            cell.text = value
