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


class CharacteristicType(str, Enum):
    PRODUCT = "product"
    PROCESS = "process"


class ControlPlanPhase(str, Enum):
    PROTOTYPE = "prototype"
    PRE_LAUNCH = "pre_launch"
    PRODUCTION = "production"
    SAFE_LAUNCH = "safe_launch"


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
class ApprovalSignature:
    signer_id: str
    signer_name: str
    role: str
    meaning: str
    authority: str
    authentication_method: str
    signed_digest: str
    executed_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


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
        policy_id = self.policy_id.strip()
        standard_version = self.standard_version.strip()
        if not policy_id or not standard_version:
            raise FmeaInputError(
                "invalid_action_priority_policy",
                "Action Priority policy ID and standard version are required.",
                "policy",
            )
        if not self.entries or len(self.entries) > 1000:
            raise FmeaInputError(
                "invalid_action_priority_policy_size",
                "Action Priority policy must contain 1 to 1000 rating combinations.",
                "entries",
            )
        keys: set[tuple[int, int, int]] = set()
        for entry in self.entries:
            ratings = entry.ratings()
            priority = entry.priority.strip()
            if not priority or len(priority) > 32:
                raise FmeaInputError(
                    "invalid_action_priority",
                    "Action Priority must contain 1 to 32 characters.",
                    "priority",
                )
            key = (ratings.severity, ratings.occurrence, ratings.detection)
            if key in keys:
                raise FmeaInputError(
                    "duplicate_action_priority_entry",
                    f"Action Priority entry {key} is duplicated.",
                    "entries",
                )
            keys.add(key)
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "standard_version", standard_version)
        object.__setattr__(
            self,
            "entries",
            tuple(
                sorted(
                    (
                        ActionPriorityEntry(
                            entry.severity,
                            entry.occurrence,
                            entry.detection,
                            entry.priority.strip(),
                        )
                        for entry in self.entries
                    ),
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

    @property
    def policy_key(self) -> str:
        return f"ap-{self.digest}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_key": self.policy_key,
            "policy_id": self.policy_id,
            "standard_version": self.standard_version,
            "digest": self.digest,
            "entries": [asdict(entry) for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ActionPriorityPolicy:
        policy = cls(
            policy_id=payload["policy_id"],
            standard_version=payload["standard_version"],
            entries=tuple(ActionPriorityEntry(**entry) for entry in payload["entries"]),
        )
        expected_digest = payload.get("digest")
        expected_key = payload.get("policy_key")
        if expected_digest is not None and expected_digest != policy.digest:
            raise FmeaInputError(
                "action_priority_policy_digest_mismatch",
                "Stored Action Priority policy digest does not match its entries.",
                "digest",
            )
        if expected_key is not None and expected_key != policy.policy_key:
            raise FmeaInputError(
                "action_priority_policy_key_mismatch",
                "Stored Action Priority policy key does not match its identity.",
                "policy_key",
            )
        return policy

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
    process_step_id: str | None = None
    characteristic_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["initial_ratings"] = self.initial_ratings.to_dict()
        payload["current_ratings"] = self.current_ratings.to_dict()
        payload["characteristic_ids"] = list(self.characteristic_ids)
        return payload


@dataclass(frozen=True, slots=True)
class ProcessStep:
    step_id: str
    sequence: int
    name: str
    operation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProcessCharacteristic:
    characteristic_id: str
    process_step_id: str
    name: str
    characteristic_type: CharacteristicType
    specification: str
    special_classification: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["characteristic_type"] = self.characteristic_type.value
        return payload


@dataclass(frozen=True, slots=True)
class AnalysisEvidenceRef:
    run_id: str
    analysis_type: str
    run_etag: str
    input_digest: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ControlPlanItem:
    control_id: str
    phase: ControlPlanPhase
    characteristic_id: str
    failure_item_ids: tuple[str, ...]
    measurement_method: str
    sample_size: int
    frequency: str
    control_method: str
    reaction_plan: str
    reaction_owner: str
    analysis_evidence: tuple[AnalysisEvidenceRef, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["phase"] = self.phase.value
        payload["failure_item_ids"] = list(self.failure_item_ids)
        payload["analysis_evidence"] = [reference.to_dict() for reference in self.analysis_evidence]
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
    action_priority_policy_key: str | None = None
    process_steps: tuple[ProcessStep, ...] = ()
    characteristics: tuple[ProcessCharacteristic, ...] = ()
    control_plan_items: tuple[ControlPlanItem, ...] = ()

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
            "action_priority_policy_key": self.action_priority_policy_key,
            "process_steps": [step.to_dict() for step in self.process_steps],
            "characteristics": [item.to_dict() for item in self.characteristics],
            "control_plan_items": [item.to_dict() for item in self.control_plan_items],
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
                    process_step_id=item.get("process_step_id"),
                    characteristic_ids=tuple(item.get("characteristic_ids", ())),
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
            action_priority_policy_key=payload.get("action_priority_policy_key"),
            process_steps=tuple(
                ProcessStep(
                    step_id=step["step_id"],
                    sequence=step["sequence"],
                    name=step["name"],
                    operation=step["operation"],
                )
                for step in payload.get("process_steps", ())
            ),
            characteristics=tuple(
                ProcessCharacteristic(
                    characteristic_id=item["characteristic_id"],
                    process_step_id=item["process_step_id"],
                    name=item["name"],
                    characteristic_type=CharacteristicType(item["characteristic_type"]),
                    specification=item["specification"],
                    special_classification=item.get("special_classification"),
                )
                for item in payload.get("characteristics", ())
            ),
            control_plan_items=tuple(
                ControlPlanItem(
                    control_id=item["control_id"],
                    phase=ControlPlanPhase(item["phase"]),
                    characteristic_id=item["characteristic_id"],
                    failure_item_ids=tuple(item["failure_item_ids"]),
                    measurement_method=item["measurement_method"],
                    sample_size=item["sample_size"],
                    frequency=item["frequency"],
                    control_method=item["control_method"],
                    reaction_plan=item["reaction_plan"],
                    reaction_owner=item["reaction_owner"],
                    analysis_evidence=tuple(
                        AnalysisEvidenceRef(**reference)
                        for reference in item.get("analysis_evidence", ())
                    ),
                )
                for item in payload.get("control_plan_items", ())
            ),
        )


def derive_seven_step_progress(study: FmeaStudySnapshot) -> tuple[SevenStepProgress, ...]:
    """Project owned FMEA facts onto the public seven-step workflow vocabulary."""

    structure_evidence_count = len(study.process_steps) or len(study.items)
    function_evidence_count = len(study.characteristics) or len(study.items)
    structure_status = (
        StepStatus.COMPLETE if structure_evidence_count else StepStatus.NOT_STARTED
    )
    function_status = (
        StepStatus.COMPLETE if function_evidence_count else StepStatus.NOT_STARTED
    )
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
        SevenStepProgress(2, SevenStepId.STRUCTURE_ANALYSIS, "Structure Analysis", structure_status, structure_evidence_count, () if structure_evidence_count else ("process_step",)),
        SevenStepProgress(3, SevenStepId.FUNCTION_ANALYSIS, "Function Analysis", function_status, function_evidence_count, () if function_evidence_count else ("process_characteristic",)),
        SevenStepProgress(4, SevenStepId.FAILURE_ANALYSIS, "Failure Analysis", item_status, len(study.items), item_gap),
        SevenStepProgress(5, SevenStepId.RISK_ANALYSIS, "Risk Analysis", item_status, len(study.items), item_gap),
        SevenStepProgress(6, SevenStepId.OPTIMIZATION, "Optimization", optimization_status, len(study.actions), optimization_gaps),
        SevenStepProgress(7, SevenStepId.RESULTS_DOCUMENTATION, "Results Documentation", documentation_status, documentation_events, documentation_gaps),
    )
