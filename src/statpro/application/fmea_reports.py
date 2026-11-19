"""Portable projections for immutable FMEA study-review snapshots."""

from __future__ import annotations

from typing import Any, Mapping

from statpro.domain.identity import input_digest


def project_fmea_review_report(review: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an owned FMEA review snapshot for the shared export renderers."""

    risk_rows = []
    for row in review["rows"]:
        failure = row["failure"]
        ratings = failure["current_ratings"]
        risk_rows.append({
            "item_id": failure["item_id"], "failure_mode": failure["failure_mode"],
            "cause": failure["cause"], "effect": failure["effect"],
            "severity": ratings["severity"], "occurrence": ratings["occurrence"],
            "detection": ratings["detection"], "rpn": ratings["rpn"],
            "action_priority": failure.get("action_priority"),
            "control_plan_ids": ", ".join(item["control_id"] for item in row["control_plan_items"]),
            "action_ids": ", ".join(item["action_id"] for item in row["actions"]),
        })
    tables = {
        "risk_analysis": risk_rows,
        "seven_step_progress": review["seven_step_progress"],
        "analysis_evidence_checks": review["analysis_evidence_checks"] or [],
        "audit_events": review["audit_events"],
    }
    report: dict[str, Any] = {
        "report_type": "statpro.fmea.export.v1",
        "run": {"run_id": review["study_id"], "storage_version": review["revision"], "etag": review["snapshot_digest"]},
        "analysis": {"analysis_type": f"fmea.{review['study_type']}", "engine_version": "workflow-v1", "input_digest": review["snapshot_digest"], "result_digest": input_digest(review)},
        "parameters": {"study_name": review["study_name"], "standard_version": review["standard_version"], "status": review["status"], "revision": review["revision"], "action_priority_policy": review["action_priority_policy"]},
        "diagnostics": {"risk_item_count": len(risk_rows), "audit_event_count": len(review["audit_events"])},
        "tables": [_table(name, rows) for name, rows in tables.items()],
        "plots": {}, "figures": [],
        "template": {"id": "standard", "name": "FMEA 검토 보고서", "intended_use": "위험 분석, 조치, 승인 및 연결 증거를 검토합니다.", "review_fields": []},
        "assumptions": [],
        "warnings": ["연결 분석 증거 중 재검증되지 않은 항목이 있습니다."] if any(item.get("status") != "verified" for item in (review["analysis_evidence_checks"] or [])) else [],
        "provenance": [], "limitations": list(review["limitations"]),
    }
    report["report_digest"] = input_digest(report)
    return report


def _table(name: str, rows: object) -> dict[str, Any]:
    source = rows if isinstance(rows, list) else [rows]
    normalized = [item if isinstance(item, dict) else {"value": item} for item in source]
    columns = list(dict.fromkeys(key for row in normalized for key in row))
    return {"name": name, "columns": columns, "row_count": len(normalized), "rows": normalized}
