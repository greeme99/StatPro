"""Owned quality metric source contracts and read-only dashboard snapshots."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Literal

from statpro.domain.errors import DomainInputError
from statpro.domain.identity import input_digest


class QualityMetricInputError(DomainInputError):
    """Raised when a quality metric source contract is not usable."""

    def __init__(self, message: str) -> None:
        super().__init__("invalid_quality_metric_source", message)


MetricStatus = Literal["good", "warning", "critical"]


@dataclass(frozen=True, slots=True)
class AnalysisRunSource:
    run_id: str
    run_etag: str
    analysis_type: str
    engine_version: str
    input_digest: str
    value_path: str


@dataclass(frozen=True, slots=True)
class QualityMetricSnapshot:
    metric_id: str
    name: str
    unit: str
    value: float
    status: MetricStatus
    source: AnalysisRunSource
    refresh_cycle: str
    owner_ref: str
    captured_at: str
    lower_warning: float | None
    lower_critical: float | None
    upper_warning: float | None
    upper_critical: float | None
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise QualityMetricInputError(f"{field} is required.")
    return normalized


def resolve_numeric_result_value(result: dict[str, Any], value_path: str) -> float:
    """Resolve one finite scalar from an allow-listed ResultBundle section."""
    parts = [part for part in value_path.split(".") if part]
    if len(parts) < 2 or parts[0] not in {"tables", "diagnostics", "parameters"}:
        raise QualityMetricInputError(
            "value_path must start with tables, diagnostics, or parameters and name a scalar field."
        )
    current: Any = result
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise QualityMetricInputError(f"value_path does not exist: {value_path}")
        current = current[part]
    if isinstance(current, bool) or not isinstance(current, (int, float)):
        raise QualityMetricInputError(f"value_path is not a numeric scalar: {value_path}")
    value = float(current)
    if not math.isfinite(value):
        raise QualityMetricInputError(f"value_path is not finite: {value_path}")
    return value


def _status(
    value: float,
    *,
    lower_warning: float | None,
    lower_critical: float | None,
    upper_warning: float | None,
    upper_critical: float | None,
) -> MetricStatus:
    if lower_critical is not None and value <= lower_critical:
        return "critical"
    if upper_critical is not None and value >= upper_critical:
        return "critical"
    if lower_warning is not None and value <= lower_warning:
        return "warning"
    if upper_warning is not None and value >= upper_warning:
        return "warning"
    return "good"


def create_quality_metric_snapshot(
    *,
    metric_id: str,
    name: str,
    unit: str,
    run_id: str,
    run_etag: str,
    result: dict[str, Any],
    value_path: str,
    refresh_cycle: str,
    owner_ref: str,
    captured_at: str,
    lower_warning: float | None = None,
    lower_critical: float | None = None,
    upper_warning: float | None = None,
    upper_critical: float | None = None,
) -> QualityMetricSnapshot:
    if (
        lower_critical is not None
        and lower_warning is not None
        and lower_critical > lower_warning
    ):
        raise QualityMetricInputError("lower_critical must not exceed lower_warning.")
    if upper_warning is not None and upper_critical is not None and upper_warning > upper_critical:
        raise QualityMetricInputError("upper_warning must not exceed upper_critical.")
    value = resolve_numeric_result_value(result, value_path)
    source = AnalysisRunSource(
        run_id=_required(run_id, "run_id"),
        run_etag=_required(run_etag, "run_etag"),
        analysis_type=_required(str(result.get("analysis_type", "")), "analysis_type"),
        engine_version=_required(str(result.get("engine_version", "")), "engine_version"),
        input_digest=_required(str(result.get("input_digest", "")), "input_digest"),
        value_path=_required(value_path, "value_path"),
    )
    digest_payload = {
        "metric_id": _required(metric_id, "metric_id"),
        "name": _required(name, "name"),
        "unit": unit.strip(),
        "value": value,
        "source": asdict(source),
        "refresh_cycle": _required(refresh_cycle, "refresh_cycle"),
        "owner_ref": _required(owner_ref, "owner_ref"),
        "captured_at": _required(captured_at, "captured_at"),
        "lower_warning": lower_warning,
        "lower_critical": lower_critical,
        "upper_warning": upper_warning,
        "upper_critical": upper_critical,
    }
    return QualityMetricSnapshot(
        metric_id=digest_payload["metric_id"],
        name=digest_payload["name"],
        unit=digest_payload["unit"],
        value=value,
        source=source,
        refresh_cycle=digest_payload["refresh_cycle"],
        owner_ref=digest_payload["owner_ref"],
        captured_at=digest_payload["captured_at"],
        lower_warning=lower_warning,
        lower_critical=lower_critical,
        upper_warning=upper_warning,
        upper_critical=upper_critical,
        status=_status(
            value,
            lower_warning=lower_warning,
            lower_critical=lower_critical,
            upper_warning=upper_warning,
            upper_critical=upper_critical,
        ),
        digest=input_digest(digest_payload),
    )
