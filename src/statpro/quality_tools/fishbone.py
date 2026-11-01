"""Revisioned Fishbone document for structuring cause hypotheses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Sequence

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest


class FishboneInputError(DomainInputError):
    """Expected, user-correctable Fishbone input failure."""


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise FishboneInputError("required_value", f"{field} is required.", field)
    return normalized


@dataclass(frozen=True, slots=True)
class FishboneCause:
    cause_id: str
    text: str
    evidence_refs: tuple[str, ...] = ()
    selected_for_verification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "evidence_refs": list(self.evidence_refs)}


@dataclass(frozen=True, slots=True)
class FishboneCategory:
    category_id: str
    name: str
    causes: tuple[FishboneCause, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "causes": [cause.to_dict() for cause in self.causes]}


@dataclass(frozen=True, slots=True)
class FishboneSnapshot:
    diagram_id: str
    title: str
    process_name: str
    problem_statement: str
    revision: int
    parent_digest: str | None
    digest: str
    categories: tuple[FishboneCategory, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "categories": [category.to_dict() for category in self.categories],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FishboneSnapshot:
        snapshot = cls(
            diagram_id=payload["diagram_id"],
            title=payload["title"],
            process_name=payload["process_name"],
            problem_statement=payload["problem_statement"],
            revision=payload["revision"],
            parent_digest=payload.get("parent_digest"),
            digest=payload["digest"],
            categories=tuple(
                FishboneCategory(
                    category_id=category["category_id"],
                    name=category["name"],
                    causes=tuple(
                        FishboneCause(
                            cause_id=cause["cause_id"],
                            text=cause["text"],
                            evidence_refs=tuple(cause.get("evidence_refs", ())),
                            selected_for_verification=cause.get(
                                "selected_for_verification", False
                            ),
                        )
                        for cause in category["causes"]
                    ),
                )
                for category in payload["categories"]
            ),
        )
        if snapshot.digest != _digest(snapshot):
            raise FishboneInputError(
                "fishbone_digest_mismatch",
                "Stored Fishbone digest does not match.",
                "digest",
            )
        return snapshot


def _digest(snapshot: FishboneSnapshot) -> str:
    payload = snapshot.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def create_fishbone(
    *,
    diagram_id: str,
    title: str,
    process_name: str,
    problem_statement: str,
    categories: Sequence[tuple[str, str]],
) -> FishboneSnapshot:
    if not 2 <= len(categories) <= 12:
        raise FishboneInputError(
            "invalid_category_count",
            "Fishbone requires between 2 and 12 categories.",
            "categories",
        )
    normalized = tuple(
        FishboneCategory(
            category_id=_required(category_id, "category_id"),
            name=_required(name, "category_name"),
        )
        for category_id, name in categories
    )
    if len({category.category_id for category in normalized}) != len(normalized):
        raise FishboneInputError(
            "duplicate_category_id", "category_id must be unique.", "categories"
        )
    draft = FishboneSnapshot(
        diagram_id=_required(diagram_id, "diagram_id"),
        title=_required(title, "title"),
        process_name=_required(process_name, "process_name"),
        problem_statement=_required(problem_statement, "problem_statement"),
        revision=1,
        parent_digest=None,
        digest="",
        categories=normalized,
    )
    return replace(draft, digest=_digest(draft))


def add_fishbone_cause(
    snapshot: FishboneSnapshot,
    *,
    category_id: str,
    cause_id: str,
    text: str,
    evidence_refs: Sequence[str] = (),
    selected_for_verification: bool = False,
) -> FishboneSnapshot:
    normalized_cause_id = _required(cause_id, "cause_id")
    if any(
        cause.cause_id == normalized_cause_id
        for category in snapshot.categories
        for cause in category.causes
    ):
        raise FishboneInputError(
            "duplicate_cause_id",
            "cause_id must be unique within a Fishbone.",
            "cause_id",
        )
    normalized_evidence = tuple(
        reference.strip() for reference in evidence_refs if reference.strip()
    )
    cause = FishboneCause(
        cause_id=normalized_cause_id,
        text=_required(text, "text"),
        evidence_refs=normalized_evidence,
        selected_for_verification=selected_for_verification,
    )
    found = False
    categories: list[FishboneCategory] = []
    for category in snapshot.categories:
        if category.category_id == category_id:
            found = True
            categories.append(replace(category, causes=(*category.causes, cause)))
        else:
            categories.append(category)
    if not found:
        raise FishboneInputError(
            "unknown_category", "category_id does not exist.", "category_id"
        )
    revised = replace(
        snapshot,
        revision=snapshot.revision + 1,
        parent_digest=snapshot.digest,
        digest="",
        categories=tuple(categories),
    )
    return replace(revised, digest=_digest(revised))
