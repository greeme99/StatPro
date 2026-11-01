"""Immutable Check Sheet document and frequency summary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ResultBundle
from statpro.version import ENGINE_VERSION


class CheckSheetInputError(DomainInputError):
    """Expected, user-correctable Check Sheet input failure."""


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise CheckSheetInputError("required_value", f"{field} is required.", field)
    return normalized


@dataclass(frozen=True, slots=True)
class CheckSheetRecord:
    record_id: str
    category: str
    count: int
    observed_at: str | None = None
    location: str | None = None
    shift: str | None = None
    lot: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CheckSheetSnapshot:
    sheet_id: str
    title: str
    process_name: str
    category_label: str
    revision: int
    parent_digest: str | None
    digest: str
    records: tuple[CheckSheetRecord, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "records": [record.to_dict() for record in self.records]}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CheckSheetSnapshot:
        snapshot = cls(
            sheet_id=payload["sheet_id"], title=payload["title"],
            process_name=payload["process_name"], category_label=payload["category_label"],
            revision=payload["revision"], parent_digest=payload.get("parent_digest"),
            digest=payload["digest"],
            records=tuple(CheckSheetRecord(**record) for record in payload["records"]),
        )
        if snapshot.digest != _digest(snapshot):
            raise CheckSheetInputError("check_sheet_digest_mismatch", "Stored Check Sheet digest does not match.", "digest")
        return snapshot


def _digest(snapshot: CheckSheetSnapshot) -> str:
    payload = snapshot.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def create_check_sheet(*, sheet_id: str, title: str, process_name: str, category_label: str) -> CheckSheetSnapshot:
    draft = CheckSheetSnapshot(
        sheet_id=_required(sheet_id, "sheet_id"), title=_required(title, "title"),
        process_name=_required(process_name, "process_name"),
        category_label=_required(category_label, "category_label"),
        revision=1, parent_digest=None, digest="",
    )
    return replace(draft, digest=_digest(draft))


def add_check_sheet_record(
    sheet: CheckSheetSnapshot, *, record_id: str, category: str, count: int,
    observed_at: str | None = None, location: str | None = None,
    shift: str | None = None, lot: str | None = None, note: str | None = None,
) -> CheckSheetSnapshot:
    if count < 1:
        raise CheckSheetInputError("invalid_count", "count must be at least 1.", "count")
    normalized_id = _required(record_id, "record_id")
    if any(record.record_id == normalized_id for record in sheet.records):
        raise CheckSheetInputError("duplicate_record_id", "record_id must be unique within a Check Sheet.", "record_id")
    record = CheckSheetRecord(
        record_id=normalized_id, category=_required(category, "category"), count=count,
        observed_at=observed_at, location=location, shift=shift, lot=lot, note=note,
    )
    revised = replace(
        sheet, revision=sheet.revision + 1, parent_digest=sheet.digest, digest="",
        records=(*sheet.records, record),
    )
    return replace(revised, digest=_digest(revised))


def summarize_check_sheet(sheet: CheckSheetSnapshot) -> ResultBundle:
    counts: dict[str, int] = {}
    for record in sheet.records:
        counts[record.category] = counts.get(record.category, 0) + record.count
    total = sum(counts.values())
    frequencies = [
        {"category": category, "count": count, "percentage": 0.0 if total == 0 else count / total * 100}
        for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    payload = {"sheet_id": sheet.sheet_id, "snapshot_digest": sheet.digest, "records": [record.to_dict() for record in sheet.records]}
    return ResultBundle(
        analysis_type="quality.check_sheet_frequency", engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={"sheet_id": sheet.sheet_id, "snapshot_digest": sheet.digest, "category_label": sheet.category_label},
        tables={"frequencies": frequencies, "summary": {"total": total, "category_count": len(counts)}},
        plots={"pareto_ready": frequencies},
        diagnostics={"record_count": len(sheet.records), "empty": total == 0},
        assumptions=("Counts represent mutually interpretable occurrence categories.",),
        warnings=("No occurrences have been recorded yet.",) if total == 0 else (),
    )
