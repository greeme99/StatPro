"""Immutable entities owned by the DMAIC project bounded context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest


class DmaicInputError(DomainInputError):
    """An expected, user-correctable DMAIC project failure."""


class DmaicProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class DmaicDocumentReference:
    document_type: str
    document_id: str
    revision: int
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DmaicProject:
    project_id: str
    title: str
    owner_ref: str
    sponsor_ref: str | None
    champion_ref: str | None
    department: str | None
    start_date: str | None
    target_end_date: str | None
    status: DmaicProjectStatus
    revision: int
    parent_digest: str | None
    digest: str
    charter: DmaicDocumentReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "owner_ref": self.owner_ref,
            "sponsor_ref": self.sponsor_ref,
            "champion_ref": self.champion_ref,
            "department": self.department,
            "start_date": self.start_date,
            "target_end_date": self.target_end_date,
            "status": self.status.value,
            "revision": self.revision,
            "parent_digest": self.parent_digest,
            "digest": self.digest,
            "charter": None if self.charter is None else self.charter.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicProject:
        reference = payload.get("charter")
        project = cls(
            project_id=payload["project_id"], title=payload["title"], owner_ref=payload["owner_ref"],
            sponsor_ref=payload.get("sponsor_ref"), champion_ref=payload.get("champion_ref"),
            department=payload.get("department"), start_date=payload.get("start_date"),
            target_end_date=payload.get("target_end_date"), status=DmaicProjectStatus(payload["status"]),
            revision=payload["revision"], parent_digest=payload.get("parent_digest"), digest=payload["digest"],
            charter=None if reference is None else DmaicDocumentReference(**reference),
        )
        if project.digest != _project_digest(project):
            raise DmaicInputError("project_digest_mismatch", "Stored DMAIC project digest does not match.", "digest")
        return project


@dataclass(frozen=True, slots=True)
class DmaicCharter:
    document_id: str
    project_id: str
    revision: int
    parent_digest: str | None
    digest: str
    business_case: str
    problem_statement: str
    scope_in: tuple[str, ...]
    scope_out: tuple[str, ...]
    success_metrics: tuple[str, ...]
    team_refs: tuple[str, ...]
    budget: str | None
    milestones: tuple[str, ...]
    risk_refs: tuple[str, ...]
    assumptions_constraints: tuple[str, ...]
    actor: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "scope_in": list(self.scope_in), "scope_out": list(self.scope_out),
                "success_metrics": list(self.success_metrics), "team_refs": list(self.team_refs),
                "milestones": list(self.milestones), "risk_refs": list(self.risk_refs),
                "assumptions_constraints": list(self.assumptions_constraints)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DmaicCharter:
        charter = cls(
            document_id=payload["document_id"], project_id=payload["project_id"], revision=payload["revision"],
            parent_digest=payload.get("parent_digest"), digest=payload["digest"],
            business_case=payload["business_case"], problem_statement=payload["problem_statement"],
            scope_in=tuple(payload["scope_in"]), scope_out=tuple(payload["scope_out"]),
            success_metrics=tuple(payload["success_metrics"]), team_refs=tuple(payload["team_refs"]),
            budget=payload.get("budget"), milestones=tuple(payload["milestones"]), risk_refs=tuple(payload["risk_refs"]),
            assumptions_constraints=tuple(payload["assumptions_constraints"]), actor=payload["actor"],
            occurred_at=payload["occurred_at"],
        )
        if charter.digest != _charter_digest(charter):
            raise DmaicInputError("charter_digest_mismatch", "Stored charter digest does not match.", "digest")
        return charter


def _project_digest(project: DmaicProject) -> str:
    payload = project.to_dict()
    payload.pop("digest")
    return input_digest(payload)


def _charter_digest(charter: DmaicCharter) -> str:
    payload = charter.to_dict()
    payload.pop("digest")
    return input_digest(payload)
