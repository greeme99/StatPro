"""Design generation for two-level full factorial experiments."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Sequence

from statpro.analyses.common import finite_values, input_digest
from statpro.domain.errors import AnalysisInputError
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_FACTORIAL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.3.1 Two-level full factorial designs",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri3331.htm",
)


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    name: str
    low: float
    high: float


def _normalize_factors(factors: Sequence[FactorDefinition]) -> list[FactorDefinition]:
    if len(factors) < 2:
        raise AnalysisInputError(
            "insufficient_factors",
            "A two-level full factorial design requires at least two factors.",
            "factors",
        )
    if len(factors) > 12:
        raise AnalysisInputError(
            "too_many_factors",
            "The bounded generator supports at most 12 factors.",
            "factors",
        )

    normalized: list[FactorDefinition] = []
    names: set[str] = set()
    for index, factor in enumerate(factors):
        name = factor.name.strip()
        if not name:
            raise AnalysisInputError(
                "empty_factor_name", f"Factor {index + 1} needs a name.", "factors"
            )
        if name in names:
            raise AnalysisInputError(
                "duplicate_factor_name", f"Factor name '{name}' is duplicated.", "factors"
            )
        low, high = finite_values([factor.low, factor.high], f"factors[{index}]")
        if low >= high:
            raise AnalysisInputError(
                "invalid_factor_levels",
                f"Factor '{name}' low level must be less than its high level.",
                f"factors[{index}]",
            )
        names.add(name)
        normalized.append(FactorDefinition(name=name, low=low, high=high))
    return normalized


def full_factorial_2level(
    factors: Sequence[FactorDefinition],
    *,
    replicates: int = 1,
    center_points: int = 0,
    randomize: bool = True,
    seed: int = 0,
) -> ResultBundle:
    """Generate a bounded, reproducible 2^k full factorial design."""

    normalized = _normalize_factors(factors)
    if isinstance(replicates, bool) or replicates < 1:
        raise AnalysisInputError(
            "invalid_replicates", "Replicates must be a positive integer.", "replicates"
        )
    if isinstance(center_points, bool) or center_points < 0:
        raise AnalysisInputError(
            "invalid_center_points",
            "Center points must be a nonnegative integer.",
            "center_points",
        )
    if not isinstance(replicates, int) or not isinstance(center_points, int):
        raise AnalysisInputError(
            "invalid_run_count", "Replicates and center points must be integers.", "replicates"
        )
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise AnalysisInputError("invalid_seed", "Random seed must be an integer.", "seed")

    factorial_run_count = 2 ** len(normalized)
    total_run_count = factorial_run_count * replicates + center_points
    if total_run_count > 100_000:
        raise AnalysisInputError(
            "design_too_large",
            "The requested design exceeds the 100,000-run safety limit.",
            "factors",
        )

    rows: list[dict[str, object]] = []
    for replicate in range(1, replicates + 1):
        for standard_index in range(factorial_run_count):
            coded = {
                factor.name: (1 if standard_index & (1 << factor_index) else -1)
                for factor_index, factor in enumerate(normalized)
            }
            actual = {
                factor.name: factor.high if coded[factor.name] == 1 else factor.low
                for factor in normalized
            }
            rows.append(
                {
                    "standard_order": standard_index + 1,
                    "replicate": replicate,
                    "point_type": "factorial",
                    "coded": coded,
                    "actual": actual,
                }
            )

    center_actual = {factor.name: (factor.low + factor.high) / 2.0 for factor in normalized}
    center_coded = {factor.name: 0 for factor in normalized}
    for center_index in range(1, center_points + 1):
        rows.append(
            {
                "standard_order": None,
                "replicate": center_index,
                "point_type": "center",
                "coded": center_coded.copy(),
                "actual": center_actual.copy(),
            }
        )

    if randomize:
        random.Random(seed).shuffle(rows)
    for run_order, row in enumerate(rows, start=1):
        row["run_order"] = run_order

    warnings: list[str] = []
    if len(normalized) >= 5:
        warnings.append(
            "NIST recommends considering fractional factorial or screening designs for five or more factors."
        )
    if not randomize:
        warnings.append(
            "Runs are not randomized; time-related nuisance factors may be confounded with factor effects."
        )

    factor_payload = [asdict(factor) for factor in normalized]
    payload = {
        "factors": factor_payload,
        "replicates": replicates,
        "center_points": center_points,
        "randomize": randomize,
        "seed": seed,
    }
    return ResultBundle(
        analysis_type="doe.full_factorial_2level",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "factors": factor_payload,
            "replicates": replicates,
            "center_points": center_points,
            "randomize": randomize,
            "seed": seed,
        },
        tables={"design": rows},
        plots={},
        diagnostics={
            "factor_count": len(normalized),
            "factorial_run_count": factorial_run_count,
            "total_run_count": total_run_count,
            "balanced": True,
            "full_factorial": True,
        },
        assumptions=(
            "Each factor has exactly two quantitative levels.",
            "The experiment can run every high/low factor combination.",
            "The supplied random seed is retained for reproducibility.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_FACTORIAL_SOURCE,),
    )
