"""Deterministic Pareto prioritization for comparable occurrence or loss categories."""

from __future__ import annotations

from collections.abc import Iterable

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION


class ParetoInputError(DomainInputError):
    """Expected, user-correctable Pareto input failure."""


def pareto_analysis(
    items: Iterable[tuple[str, float]],
    *,
    metric_kind: str = "frequency",
    threshold_percentage: float = 80.0,
    subject: str = "품질 문제",
    source_sheet_id: str | None = None,
    source_snapshot_digest: str | None = None,
) -> ResultBundle:
    """Rank categories and calculate cumulative contribution percentages.

    Duplicate category labels are merged at this owning boundary so every
    consumer sees one deterministic category identity.
    """

    if metric_kind not in {"frequency", "cost", "loss"}:
        raise ParetoInputError(
            "invalid_metric_kind",
            "metric_kind must be frequency, cost, or loss.",
            "metric_kind",
        )
    if not 0.0 < threshold_percentage <= 100.0:
        raise ParetoInputError(
            "invalid_threshold",
            "threshold_percentage must be greater than 0 and at most 100.",
            "threshold_percentage",
        )

    aggregated: dict[str, float] = {}
    for raw_category, raw_value in items:
        category = raw_category.strip()
        if not category:
            raise ParetoInputError("required_value", "category is required.", "category")
        value = float(raw_value)
        if value < 0.0:
            raise ParetoInputError(
                "negative_value", "Pareto values must be non-negative.", "value"
            )
        aggregated[category] = aggregated.get(category, 0.0) + value

    if not aggregated:
        raise ParetoInputError("empty_items", "At least one category is required.", "items")
    total = sum(aggregated.values())
    if total <= 0.0:
        raise ParetoInputError(
            "zero_total", "At least one category must have a positive value.", "items"
        )

    ranked = sorted(aggregated.items(), key=lambda item: (-item[1], item[0]))
    cumulative = 0.0
    rows: list[dict[str, object]] = []
    for rank, (category, value) in enumerate(ranked, start=1):
        cumulative_before = cumulative / total * 100.0
        cumulative += value
        rows.append(
            {
                "rank": rank,
                "category": category,
                "value": value,
                "percentage": value / total * 100.0,
                "cumulative_value": cumulative,
                "cumulative_percentage": cumulative / total * 100.0,
                "vital_few": cumulative_before < threshold_percentage,
            }
        )

    vital_few_count = sum(1 for row in rows if row["vital_few"])
    normalized_subject = subject.strip() or "품질 문제"
    payload = {
        "subject": normalized_subject,
        "metric_kind": metric_kind,
        "threshold_percentage": threshold_percentage,
        "items": [{"category": category, "value": value} for category, value in ranked],
        "source_sheet_id": source_sheet_id,
        "source_snapshot_digest": source_snapshot_digest,
    }
    warnings: list[str] = []
    if len(rows) == 1:
        warnings.append("Only one category is present; comparative prioritization is limited.")
    if any(row["value"] == 0.0 for row in rows):
        warnings.append("Zero-value categories are retained for traceability but do not affect rank.")

    return ResultBundle(
        analysis_type="quality.pareto",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "subject": normalized_subject,
            "metric_kind": metric_kind,
            "threshold_percentage": threshold_percentage,
            "source_sheet_id": source_sheet_id,
            "source_snapshot_digest": source_snapshot_digest,
        },
        tables={
            "pareto": rows,
            "summary": {
                "total": total,
                "category_count": len(rows),
                "vital_few_count": vital_few_count,
                "threshold_percentage": threshold_percentage,
            },
        },
        plots={
            "pareto": {
                "categories": [row["category"] for row in rows],
                "values": [row["value"] for row in rows],
                "cumulative_percentages": [row["cumulative_percentage"] for row in rows],
                "threshold_percentage": threshold_percentage,
            }
        },
        diagnostics={
            "merged_input_count": len(rows),
            "zero_value_count": sum(1 for row in rows if row["value"] == 0.0),
            "threshold_crossing_rank": vital_few_count,
        },
        assumptions=(
            "Category values are non-negative and measured on one comparable scale.",
            "The cumulative threshold is a prioritization aid, not evidence of causality.",
        ),
        warnings=tuple(warnings),
        provenance=(
            ProvenanceSource(
                title="NIST/SEMATECH e-Handbook: Pareto Plot",
                url="https://www.itl.nist.gov/div898/handbook/eda/section3/pareto.htm",
                authority="NIST",
            ),
        ),
    )
