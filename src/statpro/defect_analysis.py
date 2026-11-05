"""Immutable general defect-analysis revisions with owned source evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest


class DefectAnalysisInputError(DomainInputError):
    """Expected, user-correctable defect-analysis input failure."""


@dataclass(frozen=True, slots=True)
class DefectSource:
    check_sheet_id: str
    check_sheet_etag: str
    check_sheet_digest: str


@dataclass(frozen=True, slots=True)
class DefectCategory:
    category: str
    defect_count: int
    opportunity_count: int
    unit_loss: float = 0.0
    severity: int = 1


@dataclass(frozen=True, slots=True)
class DefectAnalysisSnapshot:
    analysis_id: str
    title: str
    process_name: str
    period: str
    owner_ref: str
    revision: int
    parent_digest: str | None
    digest: str
    source: DefectSource | None
    categories: tuple[DefectCategory, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DefectAnalysisSnapshot:
        source = payload.get("source")
        snapshot = cls(
            analysis_id=payload["analysis_id"],
            title=payload["title"],
            process_name=payload["process_name"],
            period=payload["period"],
            owner_ref=payload["owner_ref"],
            revision=payload["revision"],
            parent_digest=payload.get("parent_digest"),
            digest=payload["digest"],
            source=None if source is None else DefectSource(**source),
            categories=tuple(DefectCategory(**item) for item in payload["categories"]),
        )
        if snapshot.digest != _digest(snapshot):
            raise DefectAnalysisInputError(
                "defect_digest_mismatch", "Stored defect analysis digest does not match.", "digest"
            )
        return snapshot


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise DefectAnalysisInputError("required_value", f"{field} is required.", field)
    return normalized


def _digest(snapshot: DefectAnalysisSnapshot) -> str:
    payload = snapshot.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _validate_categories(categories: tuple[DefectCategory, ...]) -> tuple[DefectCategory, ...]:
    if not categories:
        raise DefectAnalysisInputError(
            "empty_categories", "At least one defect category is required.", "categories"
        )
    normalized: list[DefectCategory] = []
    seen: set[str] = set()
    for item in categories:
        category = _required(item.category, "category")
        if category in seen:
            raise DefectAnalysisInputError(
                "duplicate_category", "Defect categories must be unique.", "category"
            )
        if (
            item.defect_count < 0
            or item.opportunity_count < 1
            or item.defect_count > item.opportunity_count
        ):
            raise DefectAnalysisInputError(
                "invalid_counts",
                "defect_count must be between 0 and opportunity_count.",
                "defect_count",
            )
        if item.unit_loss < 0 or not 1 <= item.severity <= 10:
            raise DefectAnalysisInputError(
                "invalid_risk_input",
                "unit_loss must be non-negative and severity must be 1 through 10.",
                "severity",
            )
        seen.add(category)
        normalized.append(replace(item, category=category, unit_loss=float(item.unit_loss)))
    return tuple(normalized)


def create_defect_analysis(
    *,
    analysis_id: str,
    title: str,
    process_name: str,
    period: str,
    owner_ref: str,
    categories: tuple[DefectCategory, ...],
    source: DefectSource | None = None,
) -> DefectAnalysisSnapshot:
    draft = DefectAnalysisSnapshot(
        analysis_id=_required(analysis_id, "analysis_id"),
        title=_required(title, "title"),
        process_name=_required(process_name, "process_name"),
        period=_required(period, "period"),
        owner_ref=_required(owner_ref, "owner_ref"),
        revision=1,
        parent_digest=None,
        digest="",
        source=source,
        categories=_validate_categories(categories),
    )
    return replace(draft, digest=_digest(draft))


def revise_defect_analysis(
    previous: DefectAnalysisSnapshot,
    *,
    title: str,
    process_name: str,
    period: str,
    owner_ref: str,
    categories: tuple[DefectCategory, ...],
    source: DefectSource | None = None,
) -> DefectAnalysisSnapshot:
    revised = replace(
        previous,
        title=_required(title, "title"),
        process_name=_required(process_name, "process_name"),
        period=_required(period, "period"),
        owner_ref=_required(owner_ref, "owner_ref"),
        revision=previous.revision + 1,
        parent_digest=previous.digest,
        digest="",
        source=source,
        categories=_validate_categories(categories),
    )
    return replace(revised, digest=_digest(revised))


def summarize_defect_analysis(snapshot: DefectAnalysisSnapshot) -> dict[str, Any]:
    defects = sum(item.defect_count for item in snapshot.categories)
    opportunities = sum(item.opportunity_count for item in snapshot.categories)
    loss = sum(item.defect_count * item.unit_loss for item in snapshot.categories)
    rows = sorted(
        (
            {
                **asdict(item),
                "dpmo": item.defect_count / item.opportunity_count * 1_000_000,
                "estimated_loss": item.defect_count * item.unit_loss,
                "risk_score": item.defect_count * item.severity,
            }
            for item in snapshot.categories
        ),
        key=lambda row: (-row["risk_score"], -row["estimated_loss"], row["category"]),
    )
    return {
        "total_defects": defects,
        "total_opportunities": opportunities,
        "dpmo": defects / opportunities * 1_000_000,
        "estimated_loss": loss,
        "top_risk_category": rows[0]["category"],
        "categories": rows,
    }
