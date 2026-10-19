"""Shewhart variables control charts based on public NIST formulas."""

from __future__ import annotations

from statistics import fmean
from typing import Sequence

from statpro.analyses.common import finite_values, input_digest
from statpro.domain.errors import AnalysisInputError
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_IMR_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.3.2.2 Individuals Control Charts",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm",
)
NIST_XBAR_R_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.3.1.1 Shewhart X bar and R and S Control Charts",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc311.htm",
)

_XBAR_R_CONSTANTS: dict[int, tuple[float, float, float]] = {
    2: (1.880, 0.000, 3.267),
    3: (1.023, 0.000, 2.574),
    4: (0.729, 0.000, 2.282),
    5: (0.577, 0.000, 2.114),
    6: (0.483, 0.000, 2.004),
    7: (0.419, 0.076, 1.924),
    8: (0.373, 0.136, 1.864),
    9: (0.337, 0.184, 1.816),
    10: (0.308, 0.223, 1.777),
}


def individuals_moving_range(
    values: Sequence[float],
    *,
    target: float | None = None,
) -> ResultBundle:
    """Calculate an Individuals and two-point Moving Range chart."""

    observations = finite_values(values, "values")
    if len(observations) < 2:
        raise AnalysisInputError(
            "insufficient_observations",
            "I-MR requires at least two finite observations.",
            "values",
        )

    center = fmean(observations) if target is None else finite_values([target], "target")[0]
    moving_ranges = [abs(current - previous) for previous, current in zip(observations, observations[1:])]
    average_moving_range = fmean(moving_ranges)
    estimated_sigma = average_moving_range / 1.128
    individuals_ucl = center + 3.0 * estimated_sigma
    individuals_lcl = center - 3.0 * estimated_sigma
    moving_range_ucl = average_moving_range * 3.267

    individual_signals = [
        index
        for index, value in enumerate(observations)
        if value > individuals_ucl or value < individuals_lcl
    ]
    moving_range_signals = [
        index + 1 for index, value in enumerate(moving_ranges) if value > moving_range_ucl
    ]
    warnings: list[str] = []
    if average_moving_range == 0.0:
        warnings.append("All consecutive observations are equal; estimated short-term variation is zero.")

    payload = {"values": observations, "target": target}
    return ResultBundle(
        analysis_type="spc.imr",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={"moving_range_length": 2, "d2": 1.128, "d4": 3.267, "target": target},
        tables={
            "observations": observations,
            "moving_ranges": moving_ranges,
            "limits": {
                "individuals": {"center": center, "lcl": individuals_lcl, "ucl": individuals_ucl},
                "moving_range": {"center": average_moving_range, "lcl": 0.0, "ucl": moving_range_ucl},
            },
        },
        plots={
            "individuals": {"values": observations, "signals": individual_signals},
            "moving_range": {"values": moving_ranges, "signals": moving_range_signals},
        },
        diagnostics={
            "individual_signal_indices": individual_signals,
            "moving_range_signal_indices": moving_range_signals,
            "estimated_sigma": estimated_sigma,
        },
        assumptions=(
            "Observations are ordered in process time.",
            "Successive observations provide a meaningful estimate of short-term variation.",
            "Default limits use the two-point moving range and three-sigma convention.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_IMR_SOURCE,),
    )


def xbar_r(subgroups: Sequence[Sequence[float]]) -> ResultBundle:
    """Calculate Xbar and R charts for equal-sized rational subgroups."""

    if len(subgroups) < 2:
        raise AnalysisInputError(
            "insufficient_subgroups",
            "Xbar-R requires at least two rational subgroups.",
            "subgroups",
        )

    normalized = [
        finite_values(group, f"subgroups[{index}]") for index, group in enumerate(subgroups)
    ]
    subgroup_size = len(normalized[0])
    if subgroup_size not in _XBAR_R_CONSTANTS:
        raise AnalysisInputError(
            "unsupported_subgroup_size",
            "Xbar-R supports constant subgroup sizes from 2 through 10.",
            "subgroups",
        )
    if any(len(group) != subgroup_size for group in normalized):
        raise AnalysisInputError(
            "unequal_subgroup_size",
            "Every rational subgroup must contain the same number of observations.",
            "subgroups",
        )

    subgroup_means = [fmean(group) for group in normalized]
    subgroup_ranges = [max(group) - min(group) for group in normalized]
    grand_mean = fmean(subgroup_means)
    average_range = fmean(subgroup_ranges)
    a2, d3, d4 = _XBAR_R_CONSTANTS[subgroup_size]
    xbar_lcl = grand_mean - a2 * average_range
    xbar_ucl = grand_mean + a2 * average_range
    range_lcl = d3 * average_range
    range_ucl = d4 * average_range

    mean_signals = [
        index for index, value in enumerate(subgroup_means) if value < xbar_lcl or value > xbar_ucl
    ]
    range_signals = [
        index for index, value in enumerate(subgroup_ranges) if value < range_lcl or value > range_ucl
    ]
    warnings: list[str] = []
    if average_range == 0.0:
        warnings.append("Every subgroup has zero range; within-subgroup variation is zero.")

    payload = {"subgroups": normalized}
    return ResultBundle(
        analysis_type="spc.xbar_r",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={"subgroup_size": subgroup_size, "a2": a2, "d3": d3, "d4": d4},
        tables={
            "subgroups": normalized,
            "subgroup_means": subgroup_means,
            "subgroup_ranges": subgroup_ranges,
            "limits": {
                "xbar": {"center": grand_mean, "lcl": xbar_lcl, "ucl": xbar_ucl},
                "range": {"center": average_range, "lcl": range_lcl, "ucl": range_ucl},
            },
        },
        plots={
            "xbar": {"values": subgroup_means, "signals": mean_signals},
            "range": {"values": subgroup_ranges, "signals": range_signals},
        },
        diagnostics={"xbar_signal_indices": mean_signals, "range_signal_indices": range_signals},
        assumptions=(
            "Subgroups are rational and ordered in process time.",
            "Subgroup sizes are constant and no larger than 10.",
            "The range is an appropriate estimator of within-subgroup variation.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_XBAR_R_SOURCE,),
    )
