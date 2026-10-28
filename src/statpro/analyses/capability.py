"""Normal process capability for individual observations."""

from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import pairwise
from statistics import NormalDist, fmean, stdev

from statpro.analyses.common import finite_values
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_CAPABILITY_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.1.6 What is Process Capability?",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm",
)
NIST_NONNORMAL_CAPABILITY_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.1.6 What is Process Capability? (non-normal data)",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm",
)


def normal_process_capability(
    values: Sequence[float],
    *,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
) -> ResultBundle:
    """Calculate normal capability indices for ordered individual observations."""

    observations = finite_values(values, "values")
    if len(observations) < 2:
        raise AnalysisInputError(
            "insufficient_observations",
            "Normal capability requires at least two finite observations.",
            "values",
        )
    if lsl is None and usl is None:
        raise AnalysisInputError(
            "missing_specification_limit",
            "Provide at least one specification limit.",
            "lsl",
        )

    normalized_lsl = None if lsl is None else finite_values([lsl], "lsl")[0]
    normalized_usl = None if usl is None else finite_values([usl], "usl")[0]
    normalized_target = None if target is None else finite_values([target], "target")[0]
    if (
        normalized_lsl is not None
        and normalized_usl is not None
        and normalized_lsl >= normalized_usl
    ):
        raise AnalysisInputError(
            "invalid_specification_limits",
            "LSL must be less than USL.",
            "lsl",
        )

    process_mean = fmean(observations)
    moving_ranges = [
        abs(current - previous) for previous, current in pairwise(observations)
    ]
    within_sigma = fmean(moving_ranges) / 1.128
    overall_sigma = stdev(observations)
    if within_sigma == 0.0 or overall_sigma == 0.0:
        raise AnalysisInputError(
            "zero_variation",
            "Capability indices are undefined when estimated process variation is zero.",
            "values",
        )

    cpl = (
        None
        if normalized_lsl is None
        else (process_mean - normalized_lsl) / (3.0 * within_sigma)
    )
    return _normal_capability_result(
        observations,
        normalized_lsl,
        normalized_usl,
        normalized_target,
        process_mean,
        within_sigma,
        overall_sigma,
        cpl,
    )


def nonnormal_process_capability(
    values: Sequence[float],
    *,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
) -> ResultBundle:
    """Estimate nonparametric capability from empirical 0.135%, 50%, and 99.865% quantiles."""

    observations = finite_values(values, "values")
    if len(observations) < 2:
        raise AnalysisInputError(
            "insufficient_observations",
            "Non-normal capability requires at least two finite observations.",
            "values",
        )
    if lsl is None and usl is None:
        raise AnalysisInputError(
            "missing_specification_limit",
            "Provide at least one specification limit.",
            "lsl",
        )

    normalized_lsl = None if lsl is None else finite_values([lsl], "lsl")[0]
    normalized_usl = None if usl is None else finite_values([usl], "usl")[0]
    normalized_target = None if target is None else finite_values([target], "target")[0]
    if (
        normalized_lsl is not None
        and normalized_usl is not None
        and normalized_lsl >= normalized_usl
    ):
        raise AnalysisInputError(
            "invalid_specification_limits",
            "LSL must be less than USL.",
            "lsl",
        )

    lower_quantile = _linear_quantile(observations, 0.00135)
    median = _linear_quantile(observations, 0.5)
    upper_quantile = _linear_quantile(observations, 0.99865)
    equivalent_sigma = (upper_quantile - lower_quantile) / 6.0
    if equivalent_sigma == 0.0:
        raise AnalysisInputError(
            "zero_variation",
            "Non-normal capability indices are undefined when empirical tail spread is zero.",
            "values",
        )

    lower_spread = median - lower_quantile
    upper_spread = upper_quantile - median
    if normalized_lsl is not None and lower_spread == 0.0:
        raise AnalysisInputError(
            "zero_tail_spread",
            "The lower empirical tail spread is zero, so a lower non-normal capability index is undefined.",
            "values",
        )
    if normalized_usl is not None and upper_spread == 0.0:
        raise AnalysisInputError(
            "zero_tail_spread",
            "The upper empirical tail spread is zero, so an upper non-normal capability index is undefined.",
            "values",
        )

    cnpl = None if normalized_lsl is None else (median - normalized_lsl) / lower_spread
    cnpu = None if normalized_usl is None else (normalized_usl - median) / upper_spread
    cnp = (
        None
        if normalized_lsl is None or normalized_usl is None
        else (normalized_usl - normalized_lsl) / (upper_quantile - lower_quantile)
    )
    cnpk = min(value for value in (cnpl, cnpu) if value is not None)
    cnpm = None
    if normalized_lsl is not None and normalized_usl is not None and normalized_target is not None:
        cnpm = (normalized_usl - normalized_lsl) / (
            6.0 * math.sqrt(equivalent_sigma**2 + (median - normalized_target) ** 2)
        )

    observed_lower = sum(
        1 for value in observations if normalized_lsl is not None and value < normalized_lsl
    )
    observed_upper = sum(
        1 for value in observations if normalized_usl is not None and value > normalized_usl
    )
    warnings = [
        "This empirical nonparametric estimate does not fit or validate a named distribution.",
        "Capability interpretation still requires a stable, single-process population and engineering specification limits.",
    ]
    if len(observations) < 100:
        warnings.append(
            "NIST generally recommends at least 100 independent observations for capability studies; extreme empirical quantiles are especially unstable in smaller samples."
        )

    payload = {
        "values": observations,
        "lsl": normalized_lsl,
        "usl": normalized_usl,
        "target": normalized_target,
    }
    return ResultBundle(
        analysis_type="capability.nonnormal_empirical",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "lsl": normalized_lsl,
            "usl": normalized_usl,
            "target": normalized_target,
            "quantile_method": "linear_empirical_order_statistic",
            "lower_quantile_probability": 0.00135,
            "upper_quantile_probability": 0.99865,
        },
        tables={
            "summary": {
                "count": len(observations),
                "median": median,
                "lower_quantile": lower_quantile,
                "upper_quantile": upper_quantile,
                "equivalent_sigma": equivalent_sigma,
            },
            "indices": {
                "cnp": cnp,
                "cnpl": cnpl,
                "cnpu": cnpu,
                "cnpk": cnpk,
                "cnpm": cnpm,
            },
            "nonconformance": {
                "observed_lower_count": observed_lower,
                "observed_upper_count": observed_upper,
                "observed_total_ppm": (observed_lower + observed_upper) / len(observations) * 1_000_000,
            },
        },
        plots={
            "empirical_distribution": {
                "values": observations,
                "median": median,
                "lower_quantile": lower_quantile,
                "upper_quantile": upper_quantile,
                "lsl": normalized_lsl,
                "usl": normalized_usl,
                "target": normalized_target,
            }
        },
        diagnostics={
            "stability_verified": False,
            "distribution_model": "nonparametric_empirical_quantiles",
            "normality_verified": False,
        },
        assumptions=(
            "Observations are independent and represent one stable process population.",
            "Specification limits are engineering requirements, not control limits.",
            "Empirical order-statistic quantiles are an adequate nonparametric description of the process tails.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_CAPABILITY_SOURCE, NIST_NONNORMAL_CAPABILITY_SOURCE),
    )


def _normal_capability_result(
    observations: list[float],
    normalized_lsl: float | None,
    normalized_usl: float | None,
    normalized_target: float | None,
    process_mean: float,
    within_sigma: float,
    overall_sigma: float,
    cpl: float | None,
) -> ResultBundle:
    cpu = (
        None
        if normalized_usl is None
        else (normalized_usl - process_mean) / (3.0 * within_sigma)
    )
    ppl = (
        None
        if normalized_lsl is None
        else (process_mean - normalized_lsl) / (3.0 * overall_sigma)
    )
    ppu = (
        None
        if normalized_usl is None
        else (normalized_usl - process_mean) / (3.0 * overall_sigma)
    )
    cp = (
        None
        if normalized_lsl is None or normalized_usl is None
        else (normalized_usl - normalized_lsl) / (6.0 * within_sigma)
    )
    pp = (
        None
        if normalized_lsl is None or normalized_usl is None
        else (normalized_usl - normalized_lsl) / (6.0 * overall_sigma)
    )
    cpk = min(value for value in (cpl, cpu) if value is not None)
    ppk = min(value for value in (ppl, ppu) if value is not None)
    cpm = None
    if normalized_lsl is not None and normalized_usl is not None and normalized_target is not None:
        denominator = 6.0 * math.sqrt(overall_sigma**2 + (process_mean - normalized_target) ** 2)
        cpm = (normalized_usl - normalized_lsl) / denominator

    distribution = NormalDist(mu=process_mean, sigma=overall_sigma)
    expected_lower = 0.0 if normalized_lsl is None else distribution.cdf(normalized_lsl)
    expected_upper = 0.0 if normalized_usl is None else 1.0 - distribution.cdf(normalized_usl)
    observed_lower = sum(
        1 for value in observations if normalized_lsl is not None and value < normalized_lsl
    )
    observed_upper = sum(
        1 for value in observations if normalized_usl is not None and value > normalized_usl
    )

    warnings = [
        "Capability interpretation requires a stable process and an approximately normal distribution."
    ]
    if len(observations) < 50:
        warnings.append(
            "NIST notes that capability estimates generally need about 50 independent observations."
        )

    payload = {
        "values": observations,
        "lsl": normalized_lsl,
        "usl": normalized_usl,
        "target": normalized_target,
    }
    return ResultBundle(
        analysis_type="capability.normal_individuals",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "lsl": normalized_lsl,
            "usl": normalized_usl,
            "target": normalized_target,
            "within_sigma_method": "average_moving_range_2/d2",
            "d2": 1.128,
        },
        tables={
            "summary": {
                "count": len(observations),
                "mean": process_mean,
                "within_sigma": within_sigma,
                "overall_sigma": overall_sigma,
            },
            "indices": {
                "cp": cp,
                "cpl": cpl,
                "cpu": cpu,
                "cpk": cpk,
                "pp": pp,
                "ppl": ppl,
                "ppu": ppu,
                "ppk": ppk,
                "cpm": cpm,
            },
            "nonconformance": {
                "observed_lower_count": observed_lower,
                "observed_upper_count": observed_upper,
                "observed_total_ppm": (observed_lower + observed_upper) / len(observations) * 1_000_000,
                "expected_lower_ppm": expected_lower * 1_000_000,
                "expected_upper_ppm": expected_upper * 1_000_000,
                "expected_total_ppm": (expected_lower + expected_upper) * 1_000_000,
            },
        },
        plots={
            "distribution": {
                "values": observations,
                "mean": process_mean,
                "lsl": normalized_lsl,
                "usl": normalized_usl,
                "target": normalized_target,
            }
        },
        diagnostics={
            "stability_verified": False,
            "normality_verified": False,
            "within_sigma_method": "average_moving_range_2/d2",
        },
        assumptions=(
            "Observations are independent and ordered in process time.",
            "The process is stable before capability is interpreted.",
            "The process distribution is approximately normal.",
            "Specification limits are engineering requirements, not control limits.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_CAPABILITY_SOURCE,),
    )


def _linear_quantile(values: Sequence[float], probability: float) -> float:
    """Return the linearly interpolated empirical quantile for one finite sample."""

    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    return ordered[lower_index] + fraction * (ordered[upper_index] - ordered[lower_index])
