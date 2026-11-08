"""Transparent cost-benefit calculations for DMAIC improvement decisions."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from statpro.dmaic.models import DmaicDocumentReference, DmaicInputError
from statpro.domain.identity import input_digest


@dataclass(frozen=True, slots=True)
class CostBenefitItem:
    name: str
    amount: float
    recurrence: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DmaicCostBenefitAnalysis:
    """Immutable input-scenario record; it does not represent financial approval."""

    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    currency: str
    analysis_months: int
    costs: tuple[CostBenefitItem, ...]
    benefits: tuple[CostBenefitItem, ...]
    summary: dict[str, object]
    assumptions: tuple[str, ...]
    source_documents: tuple[DmaicDocumentReference, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "project_id": self.project_id,
            "revision": self.revision,
            "parent_digest": self.parent_digest,
            "digest": self.digest,
            "currency": self.currency,
            "analysis_months": self.analysis_months,
            "costs": [item.to_dict() for item in self.costs],
            "benefits": [item.to_dict() for item in self.benefits],
            "summary": self.summary,
            "assumptions": list(self.assumptions),
            "source_documents": [item.to_dict() for item in self.source_documents],
            "actor": self.actor,
            "occurred_at": self.occurred_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DmaicCostBenefitAnalysis":
        analysis = cls(
            document_id=str(payload["document_id"]), project_id=str(payload["project_id"]),
            revision=int(payload["revision"]), parent_digest=payload.get("parent_digest") if isinstance(payload.get("parent_digest"), str) else None,
            digest=str(payload["digest"]), currency=str(payload["currency"]), analysis_months=int(payload["analysis_months"]),
            costs=tuple(CostBenefitItem(**item) for item in payload["costs"]),  # type: ignore[arg-type]
            benefits=tuple(CostBenefitItem(**item) for item in payload["benefits"]),  # type: ignore[arg-type]
            summary=dict(payload["summary"]), assumptions=tuple(str(item) for item in payload["assumptions"]),  # type: ignore[arg-type]
            source_documents=tuple(DmaicDocumentReference(**item) for item in payload.get("source_documents", [])),  # type: ignore[arg-type]
            actor=str(payload["actor"]), occurred_at=str(payload["occurred_at"]),
        )
        if analysis.digest != _cost_benefit_digest(analysis):
            raise DmaicInputError("cost_benefit_digest_mismatch", "Stored cost-benefit digest does not match.", "digest")
        return analysis


def _cost_benefit_digest(analysis: DmaicCostBenefitAnalysis) -> str:
    payload = analysis.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _items(items: tuple[CostBenefitItem, ...], field: str) -> tuple[CostBenefitItem, ...]:
    if not items:
        raise DmaicInputError("required", f"{field} requires at least one item.", field)
    normalized: list[CostBenefitItem] = []
    for index, item in enumerate(items):
        name = item.name.strip()
        if not name:
            raise DmaicInputError("required", "Cost-benefit item needs a name.", f"{field}[{index}].name")
        if not math.isfinite(item.amount) or item.amount < 0:
            raise DmaicInputError("invalid_amount", "Cost-benefit amount must be finite and nonnegative.", f"{field}[{index}].amount")
        if item.recurrence not in {"one_time", "monthly", "annual"}:
            raise DmaicInputError("invalid_recurrence", "Unsupported recurrence.", f"{field}[{index}].recurrence")
        normalized.append(CostBenefitItem(name, item.amount, item.recurrence))
    return tuple(normalized)


def summarize_cost_benefit(
    *, costs: tuple[CostBenefitItem, ...], benefits: tuple[CostBenefitItem, ...], analysis_months: int
) -> dict[str, object]:
    """Calculate an input-based scenario summary; it does not validate financial realization."""
    if isinstance(analysis_months, bool) or not isinstance(analysis_months, int) or analysis_months < 1:
        raise DmaicInputError("invalid_analysis_months", "analysis_months must be a positive integer.", "analysis_months")
    normalized_costs = _items(costs, "costs")
    normalized_benefits = _items(benefits, "benefits")

    def total(items: tuple[CostBenefitItem, ...]) -> float:
        return sum(item.amount * (1 if item.recurrence == "one_time" else analysis_months if item.recurrence == "monthly" else analysis_months / 12) for item in items)

    cost_total = total(normalized_costs)
    benefit_total = total(normalized_benefits)
    net_benefit = benefit_total - cost_total
    one_time_cost = sum(item.amount for item in normalized_costs if item.recurrence == "one_time")
    monthly_benefit = sum(item.amount for item in normalized_benefits if item.recurrence == "monthly") + sum(item.amount / 12 for item in normalized_benefits if item.recurrence == "annual")
    return {
        "analysis_months": analysis_months,
        "cost_total": cost_total,
        "benefit_total": benefit_total,
        "net_benefit": net_benefit,
        "roi_percent": None if cost_total == 0 else (net_benefit / cost_total) * 100,
        "estimated_payback_months": None if monthly_benefit <= 0 else one_time_cost / monthly_benefit,
        "limitations": [
            "입력한 비용·편익과 발생 주기만 합산한 시나리오입니다.",
            "실현 효과, 회계 승인, 할인율, 세금, 현금흐름 또는 투자 승인을 자동으로 판정하지 않습니다.",
        ],
    }
