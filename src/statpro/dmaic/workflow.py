"""State transitions for DMAIC project documents."""

from __future__ import annotations

from dataclasses import replace

from statpro.dmaic.models import (
    DmaicCharter,
    DmaicDocumentReference,
    DmaicInputError,
    DmaicProject,
    DmaicProjectStatus,
    _charter_digest,
    _project_digest,
)


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise DmaicInputError("required", f"{field} is required.", field)
    return normalized


def _optional(value: str | None) -> str | None:
    return None if value is None or not value.strip() else value.strip()


def _items(values: tuple[str, ...], field: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_required(value, field) for value in values))


def create_project(*, project_id: str, title: str, owner_ref: str, sponsor_ref: str | None = None,
                   champion_ref: str | None = None, department: str | None = None,
                   start_date: str | None = None, target_end_date: str | None = None) -> DmaicProject:
    project = DmaicProject(project_id=_required(project_id, "project_id"), title=_required(title, "title"),
        owner_ref=_required(owner_ref, "owner_ref"), sponsor_ref=_optional(sponsor_ref), champion_ref=_optional(champion_ref),
        department=_optional(department), start_date=_optional(start_date), target_end_date=_optional(target_end_date),
        status=DmaicProjectStatus.DRAFT, revision=1, parent_digest=None, digest="", charter=None)
    return replace(project, digest=_project_digest(project))


def save_charter(project: DmaicProject, *, business_case: str, problem_statement: str,
                 scope_in: tuple[str, ...], scope_out: tuple[str, ...], success_metrics: tuple[str, ...],
                 team_refs: tuple[str, ...], budget: str | None, milestones: tuple[str, ...],
                 risk_refs: tuple[str, ...], assumptions_constraints: tuple[str, ...], actor: str,
                 occurred_at: str) -> tuple[DmaicProject, DmaicCharter]:
    previous = project.charter
    revision = 1 if previous is None else previous.revision + 1
    charter = DmaicCharter(document_id=f"{project.project_id}-charter-r{revision}", project_id=project.project_id,
        revision=revision, parent_digest=None if previous is None else previous.digest, digest="",
        business_case=_required(business_case, "business_case"), problem_statement=_required(problem_statement, "problem_statement"),
        scope_in=_items(scope_in, "scope_in"), scope_out=_items(scope_out, "scope_out"),
        success_metrics=_items(success_metrics, "success_metrics"), team_refs=_items(team_refs, "team_refs"), budget=_optional(budget),
        milestones=_items(milestones, "milestones"), risk_refs=_items(risk_refs, "risk_refs"),
        assumptions_constraints=_items(assumptions_constraints, "assumptions_constraints"), actor=_required(actor, "actor"),
        occurred_at=_required(occurred_at, "occurred_at"))
    charter = replace(charter, digest=_charter_digest(charter))
    reference = DmaicDocumentReference("project_charter", charter.document_id, charter.revision, charter.digest)
    revised = replace(project, revision=project.revision + 1, parent_digest=project.digest, digest="", charter=reference)
    return replace(revised, digest=_project_digest(revised)), charter
