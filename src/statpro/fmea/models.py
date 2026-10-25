"""Immutable entities and value objects owned by the FMEA bounded context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest


class FmeaInputError(DomainInputError):
    """An expected, user-correctable FMEA workflow failure."""


class StudyType(str, Enum):
    DESIGN = "design"
    PROCESS = "process"


class StudyStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ActionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class SevenStepId(str, Enum):
    PLANNING_AND_PREPARATION = "planning_and_preparation"
    STRUCTURE_ANALYSIS = "structure_analysis"
    FUNCTION_ANALYSIS = "function_analysis"
    FAILURE_ANALYSIS = "failure_analysis"
    RISK_ANALYSIS = "risk_analysis"
    OPTIMIZATION = "optimization"
    RESULTS_DOCUMENTATION = "results_documentation"


class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class SevenStepProgress:
    step_number: int
    step_id: SevenStepId
    title: str
    status: StepStatus
    evidence_count: int
    gaps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "step_id": self.step_id.value,
            "title": self.title,
            "status": self.status.value,
            "evidence_count": self.evidence_count,
            "gaps": list(self.gaps),
        }


@dataclass(frozen=True, slots=True)
class RiskRatings:
    severity: int
    occurrence: int
    detection: int

    def __post_init__(self) -> None:
        for field, value in (
            ("severity", self.severity),
            ("occurrence", self.occurrence),
            ("detection", self.detection),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10:
                raise FmeaInputError(
                    "invalid_risk_rating", f"{field} must be an integer from 1 to 10.", field
                )

    @property
    def rpn(self) -> int:
        return self.severity * self.occurrence * self.detection

    def to_dict(self) -> dict[str, int]:
        return {
            "severity": self.severity,
            "occurrence": self.occurrence,
            "detection": self.detection,
            "rpn": self.rpn,
        }


@dataclass(frozen=True, slots=True)
class ActionPriorityEntry:
    severity: int
    occurrence: int
    detection: int
    priority: str

    def ratings(self) -> RiskRatings:
        return RiskRatings(self.severity, self.occurrence, self.detection)


@dataclass(frozen=True, slots=True)
class ActionPriorityPolicy:
    policy_id: str
    standard_version: str
    entries: tuple[ActionPriorityEntry, ...]

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.standard_version.strip():
            raise FmeaInputError(
                "invalid_action_priority_policy",
                "Action Priority policy ID and standard version are required.",
                "policy",
            )
        keys: set[tuple[int, int, int]] = set()
        for entry in self.entries:
            ratings = entry.ratings()
            if not entry.priority.strip():
                raise FmeaInputError(
                    "invalid_action_priority", "Action Priority cannot be empty.", "priority"
                )
            key = (ratings.severity, ratings.occurrence, ratings.detection)
            if key in keys:
                raise FmeaInputError(
                    "duplicate_action_priority_entry",
                    f"Action Priority entry {key} is duplicated.",
                    "entries",
                )
            keys.add(key)
        object.__setattr__(
            self,
            "entries",
            tuple(
                sorted(
                    self.entries,
                    key=lambda entry: (
                        entry.severity,
                        entry.occurrence,
                        entry.detection,
                        entry.priority,
                    ),
                )
            ),
        )

    @property
    def digest(self) -> str:
        return input_digest(
            {
                "policy_id": self.policy_id,
                "standard_version": self.standard_version,
                "entries": [asdict(entry) for entry in self.entries],
            }
        )

    def evaluate(self, ratings: RiskRatings) -> str | None:
        key = (ratings.severity, ratings.occurrence, ratings.detection)
        for entry in self.entries:
            if (entry.severity, entry.occurrence, entry.detection) == key:
                return entry.priority
        return None


@dataclass(frozen=True, slots=True)
class FailureAnalysis:
    item_id: str
    structure_element: str
    function: str
    requirement: str
    failure_mode: str
    effect: str
    cause: str
    prevention_control: str
    detection_control: str
    initial_ratings: RiskRatings
    current_ratings: RiskRatings
    action_priority: str | None
    action_priority_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["initial_ratings"] = self.initial_ratings.to_dict()
        payload["current_ratings"] = self.current_ratings.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class RecommendedAction:
    action_id: str
    item_id: str
    description: str
    owner: str
    due_date: str
    status: ActionStatus
    result: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class AuditEvent:
    sequence: int
    event_type: str
    actor: str
    occurred_at: str
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FmeaStudySnapshot:
    study_id: str
    name: str
    study_type: StudyType
    standard_version: str
    status: StudyStatus
    revision: int
    parent_digest: str | None
    digest: str
    items: tuple[FailureAnalysis, ...]
    actions: tuple[RecommendedAction, ...]
    audit_events: tuple[AuditEvent, ...]
    action_priority_policy_id: str | None = None
    action_priority_policy_digest: str | None = None

    @property
    def seven_step_progress(self) -> tuple[SevenStepProgress, ...]:
        return derive_seven_step_progress(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "name": self.name,
            "study_type": self.study_type.value,
            "standard_version": self.standard_version,
            "status": self.status.value,
            "revision": self.revision,
            "parent_digest": self.parent_digest,
            "digest": self.digest,
            "items": [item.to_dict() for item in self.items],
            "actions": [action.to_dict() for action in self.actions],
            "audit_events": [asdict(event) for event in self.audit_events],
            "action_priority_policy_id": self.action_priority_policy_id,
            "action_priority_policy_digest": self.action_priority_policy_digest,
            "seven_step_progress": [step.to_dict() for step in self.seven_step_progress],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FmeaStudySnapshot:
        """Restore a persisted snapshot at the bounded-context boundary."""

        def ratings(value: dict[str, Any]) -> RiskRatings:
            return RiskRatings(
                severity=value["severity"],
                occurrence=value["occurrence"],
                detection=value["detection"],
            )

        return cls(
            study_id=payload["study_id"],
            name=payload["name"],
            study_type=StudyType(payload["study_type"]),
            standard_version=payload["standard_version"],
            status=StudyStatus(payload["status"]),
            revision=payload["revision"],
            parent_digest=payload["parent_digest"],
            digest=payload["digest"],
            items=tuple(
                FailureAnalysis(
                    item_id=item["item_id"],
                    structure_element=item["structure_element"],
                    function=item["function"],
                    requirement=item["requirement"],
                    failure_mode=item["failure_mode"],
                    effect=item["effect"],
                    cause=item["cause"],
                    prevention_control=item["prevention_control"],
                    detection_control=item["detection_control"],
                    initial_ratings=ratings(item["initial_ratings"]),
                    current_ratings=ratings(item["current_ratings"]),
                    action_priority=item["action_priority"],
                    action_priority_reason=item["action_priority_reason"],
                )
                for item in payload["items"]
            ),
            actions=tuple(
                RecommendedAction(
                    action_id=action["action_id"],
                    item_id=action["item_id"],
                    description=action["description"],
                    owner=action["owner"],
                    due_date=action["due_date"],
                    status=ActionStatus(action["status"]),
                    result=action["result"],
                    evidence_refs=tuple(action["evidence_refs"]),
                )
                for action in payload["actions"]
            ),
            audit_events=tuple(
                AuditEvent(
                    sequence=event["sequence"],
                    event_type=event["event_type"],
                    actor=event["actor"],
                    occurred_at=event["occurred_at"],
                    details=event["details"],
                )
                for event in payload["audit_events"]
            ),
            action_priority_policy_id=payload.get("action_priority_policy_id"),
            action_priority_policy_digest=payload.get("action_priority_policy_digest"),
        )


def derive_seven_step_progress(study: FmeaStudySnapshot) -> tuple[SevenStepProgress, ...]:
    """Project owned FMEA facts onto the public seven-step workflow vocabulary."""

    item_status = StepStatus.COMPLETE if study.items else StepStatus.NOT_STARTED
    item_gap = () if study.items else ("failure_analysis_item",)
    terminal_actions = {ActionStatus.COMPLETE, ActionStatus.CANCELLED}
    if not study.actions:
        optimization_status = StepStatus.NOT_STARTED
        optimization_gaps = ("recommended_action",)
    elif all(action.status in terminal_actions for action in study.actions):
        optimization_status = StepStatus.COMPLETE
        optimization_gaps = ()
    else:
        optimization_status = StepStatus.IN_PROGRESS
        optimization_gaps = tuple(
            action.action_id for action in study.actions if action.status not in terminal_actions
        )

    documentation_events = sum(
        event.event_type in {"study_submitted", "study_approved"}
        for event in study.audit_events
    )
    if study.status in {StudyStatus.APPROVED, StudyStatus.ARCHIVED}:
        documentation_status = StepStatus.COMPLETE
        documentation_gaps: tuple[str, ...] = ()
    elif study.status == StudyStatus.IN_REVIEW:
        documentation_status = StepStatus.IN_PROGRESS
        documentation_gaps = ("approval",)
    else:
        documentation_status = StepStatus.NOT_STARTED
        documentation_gaps = ("review_submission",)

    return (
        SevenStepProgress(1, SevenStepId.PLANNING_AND_PREPARATION, "Planning and Preparation", StepStatus.COMPLETE, 1),
        SevenStepProgress(2, SevenStepId.STRUCTURE_ANALYSIS, "Structure Analysis", item_status, len(study.items), item_gap),
        SevenStepProgress(3, SevenStepId.FUNCTION_ANALYSIS, "Function Analysis", item_status, len(study.items), item_gap),
        SevenStepProgress(4, SevenStepId.FAILURE_ANALYSIS, "Failure Analysis", item_status, len(study.items), item_gap),
        SevenStepProgress(5, SevenStepId.RISK_ANALYSIS, "Risk Analysis", item_status, len(study.items), item_gap),
        SevenStepProgress(6, SevenStepId.OPTIMIZATION, "Optimization", optimization_status, len(study.actions), optimization_gaps),
        SevenStepProgress(7, SevenStepId.RESULTS_DOCUMENTATION, "Results Documentation", documentation_status, documentation_events, documentation_gaps),
    )
