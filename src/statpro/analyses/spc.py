"""Shewhart variables control charts based on public NIST formulas."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise
from math import exp, lgamma, sqrt
from statistics import fmean, stdev
from typing import Literal

from statpro.analyses.common import finite_values
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
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
NIST_XBAR_S_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.3.2.1 Shewhart X bar and S Control Charts",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc321.htm",
)
MINITAB_XBAR_S_SOURCE = ProvenanceSource(
    title="Minitab public documentation: Overview for Xbar-S Chart",
    url=(
        "https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/"
        "control-charts/how-to/variables-charts-for-subgroups/xbar-s-chart/before-you-start/overview/"
    ),
)
NIST_WECO_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.3.2 Variables Control Charts and WECO Rules",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm",
)
NIST_ATTRIBUTE_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.3.3 What are Attributes Control Charts?",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc33.htm",
)
NIST_POISSON_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 6.3.3.1 Counts Control Charts",
    url="https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc331.htm",
)
MINITAB_SPECIAL_CAUSE_SOURCE = ProvenanceSource(
    title="Minitab public documentation: Tests for special causes in control charts",
    url="https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/supporting-topics/basics/using-tests-for-special-causes/",
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


def _nonnegative_integers(values: Sequence[object], field: str) -> list[int]:
    normalized = finite_values(values, field)
    integers: list[int] = []
    for index, value in enumerate(normalized):
        if value < 0.0 or not value.is_integer():
            raise AnalysisInputError(
                "invalid_count",
                f"Value at index {index} must be a nonnegative integer count.",
                field,
            )
        integers.append(int(value))
    return integers


def _positive_integers(values: Sequence[object], field: str) -> list[int]:
    normalized = _nonnegative_integers(values, field)
    for index, value in enumerate(normalized):
        if value == 0:
            raise AnalysisInputError(
                "invalid_sample_size",
                f"Sample size at index {index} must be a positive integer.",
                field,
            )
    return normalized


def _binomial_attribute_chart(
    nonconforming: Sequence[object],
    sample_sizes: Sequence[object],
    *,
    chart: Literal["p", "np"],
) -> ResultBundle:
    """Own normalization and result construction for binomial attribute charts."""

    counts = _nonnegative_integers(nonconforming, "nonconforming")
    sizes = _positive_integers(sample_sizes, "sample_sizes")
    if len(counts) < 2:
        raise AnalysisInputError(
            "insufficient_subgroups",
            "Attribute control charts require at least two ordered subgroups.",
            "nonconforming",
        )
    if len(counts) != len(sizes):
        raise AnalysisInputError(
            "mismatched_subgroups",
            "Nonconforming counts and sample sizes must have the same length.",
            "sample_sizes",
        )
    for index, (count, size) in enumerate(zip(counts, sizes, strict=True)):
        if count > size:
            raise AnalysisInputError(
                "count_exceeds_sample_size",
                f"Nonconforming count at index {index} exceeds its sample size.",
                "nonconforming",
            )
    if chart == "np" and any(size != sizes[0] for size in sizes[1:]):
        raise AnalysisInputError(
            "unequal_sample_size",
            "An np chart requires the same inspected sample size in every subgroup; use a p chart when sample sizes vary.",
            "sample_sizes",
        )

    total_nonconforming = sum(counts)
    total_inspected = sum(sizes)
    pooled_proportion = total_nonconforming / total_inspected
    points: list[dict[str, object]] = []
    signal_indices: list[int] = []
    unclamped_limits: list[dict[str, float]] = []

    for index, (count, size) in enumerate(zip(counts, sizes, strict=True)):
        if chart == "p":
            statistic = count / size
            center = pooled_proportion
            sigma = sqrt(pooled_proportion * (1.0 - pooled_proportion) / size)
            lower_bound, upper_bound = 0.0, 1.0
        else:
            statistic = float(count)
            center = size * pooled_proportion
            sigma = sqrt(size * pooled_proportion * (1.0 - pooled_proportion))
            lower_bound, upper_bound = 0.0, float(size)
        raw_lcl = center - 3.0 * sigma
        raw_ucl = center + 3.0 * sigma
        lcl = max(lower_bound, raw_lcl)
        ucl = min(upper_bound, raw_ucl)
        signal = statistic < lcl or statistic > ucl
        if signal:
            signal_indices.append(index)
        points.append(
            {
                "index": index,
                "event_count": count,
                "opportunity": size,
                "nonconforming": count,
                "sample_size": size,
                "statistic": statistic,
                "center": center,
                "lcl": lcl,
                "ucl": ucl,
                "signal": signal,
            }
        )
        unclamped_limits.append({"lcl": raw_lcl, "ucl": raw_ucl})

    warnings: list[str] = []
    if pooled_proportion in {0.0, 1.0}:
        warnings.append(
            "The pooled nonconforming proportion is at a boundary, so estimated binomial variation and all three-sigma limits collapse."
        )
    if any(
        size * pooled_proportion < 5.0 or size * (1.0 - pooled_proportion) < 5.0
        for size in sizes
    ):
        warnings.append(
            "At least one subgroup has fewer than five expected conforming or nonconforming units; the normal-approximation limits may be inaccurate."
        )

    analysis_type = f"spc.{chart}_chart"
    payload = {"nonconforming": counts, "sample_sizes": sizes, "chart": chart}
    return ResultBundle(
        analysis_type=analysis_type,
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "chart": chart,
            "distribution": "binomial",
            "sigma_multiplier": 3.0,
            "limit_method": "normal_approximation",
            "sample_size_mode": "variable" if len(set(sizes)) > 1 else "constant",
        },
        tables={
            "chart_points": points,
            "summary": {
                "total_nonconforming": total_nonconforming,
                "total_inspected": total_inspected,
                "pooled_proportion": pooled_proportion,
            },
        },
        plots={
            "attribute_chart": {
                "points": points,
                "signal_indices": signal_indices,
            }
        },
        diagnostics={
            "subgroup_count": len(points),
            "signal_indices": signal_indices,
            "signal_count": len(signal_indices),
            "unclamped_limits": unclamped_limits,
            "limits_clamped_to_parameter_space": any(
                raw["lcl"] < 0.0
                or raw["ucl"] > (1.0 if chart == "p" else float(sizes[index]))
                for index, raw in enumerate(unclamped_limits)
            ),
        },
        assumptions=(
            "Subgroups are ordered in process time and represent comparable process conditions.",
            "Each inspected unit is classified once as conforming or nonconforming.",
            "Within each subgroup, unit classifications are independent with a stable nonconforming probability.",
            "Phase I center lines use the pooled nonconforming proportion from all supplied subgroups.",
            "Signals identify investigation candidates and do not by themselves prove a special cause.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_ATTRIBUTE_SOURCE,),
    )


def p_chart(
    nonconforming: Sequence[object], sample_sizes: Sequence[object]
) -> ResultBundle:
    """Calculate a p chart for subgroup nonconforming proportions."""

    return _binomial_attribute_chart(nonconforming, sample_sizes, chart="p")


def np_chart(
    nonconforming: Sequence[object], sample_sizes: Sequence[object]
) -> ResultBundle:
    """Calculate an np chart for subgroup nonconforming counts."""

    return _binomial_attribute_chart(nonconforming, sample_sizes, chart="np")


def _poisson_attribute_chart(
    defects: Sequence[object],
    inspection_units: Sequence[object],
    *,
    chart: Literal["c", "u"],
) -> ResultBundle:
    """Own normalization and calculation for Poisson attribute charts."""

    counts = _nonnegative_integers(defects, "defects")
    units = finite_values(inspection_units, "inspection_units")
    if len(counts) < 2:
        raise AnalysisInputError(
            "insufficient_subgroups",
            "Attribute control charts require at least two ordered subgroups.",
            "defects",
        )
    if len(counts) != len(units):
        raise AnalysisInputError(
            "mismatched_subgroups",
            "Defect counts and inspection units must have the same length.",
            "inspection_units",
        )
    for index, unit_count in enumerate(units):
        if unit_count <= 0.0:
            raise AnalysisInputError(
                "invalid_inspection_units",
                f"Inspection units at index {index} must be positive.",
                "inspection_units",
            )
    if chart == "c" and any(unit_count != units[0] for unit_count in units[1:]):
        raise AnalysisInputError(
            "unequal_opportunity",
            "A c chart requires equal inspection opportunity in every subgroup; use a u chart when opportunity varies.",
            "inspection_units",
        )

    total_defects = sum(counts)
    total_units = sum(units)
    average_rate = total_defects / total_units
    points: list[dict[str, object]] = []
    signal_indices: list[int] = []
    unclamped_limits: list[dict[str, float]] = []
    for index, (count, unit_count) in enumerate(zip(counts, units, strict=True)):
        if chart == "c":
            statistic = float(count)
            center = average_rate * unit_count
            sigma = sqrt(center)
        else:
            statistic = count / unit_count
            center = average_rate
            sigma = sqrt(average_rate / unit_count)
        raw_lcl = center - 3.0 * sigma
        raw_ucl = center + 3.0 * sigma
        lcl = max(0.0, raw_lcl)
        ucl = raw_ucl
        signal = statistic < lcl or statistic > ucl
        if signal:
            signal_indices.append(index)
        points.append(
            {
                "index": index,
                "event_count": count,
                "opportunity": unit_count,
                "defects": count,
                "inspection_units": unit_count,
                "statistic": statistic,
                "center": center,
                "lcl": lcl,
                "ucl": ucl,
                "signal": signal,
            }
        )
        unclamped_limits.append({"lcl": raw_lcl, "ucl": raw_ucl})

    warnings: list[str] = []
    if average_rate == 0.0:
        warnings.append(
            "The estimated defect rate is zero, so estimated Poisson variation and all three-sigma limits collapse."
        )
    if any(unit_count * average_rate < 5.0 for unit_count in units):
        warnings.append(
            "At least one subgroup has fewer than five expected defects; the normal-approximation limits may be inaccurate."
        )

    payload = {"defects": counts, "inspection_units": units, "chart": chart}
    return ResultBundle(
        analysis_type=f"spc.{chart}_chart",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "chart": chart,
            "distribution": "poisson",
            "sigma_multiplier": 3.0,
            "limit_method": "normal_approximation",
            "opportunity_mode": "variable" if len(set(units)) > 1 else "constant",
        },
        tables={
            "chart_points": points,
            "summary": {
                "total_defects": total_defects,
                "total_inspection_units": total_units,
                "average_defects_per_unit": average_rate,
            },
        },
        plots={
            "attribute_chart": {
                "points": points,
                "signal_indices": signal_indices,
            }
        },
        diagnostics={
            "subgroup_count": len(points),
            "signal_indices": signal_indices,
            "signal_count": len(signal_indices),
            "unclamped_limits": unclamped_limits,
            "limits_clamped_to_parameter_space": any(
                raw["lcl"] < 0.0 for raw in unclamped_limits
            ),
        },
        assumptions=(
            "Subgroups are ordered in process time and represent comparable process conditions.",
            "Defects are discrete events and more than one defect may occur on an inspected unit.",
            "Defects occur independently at a stable average Poisson rate within the Phase I baseline.",
            "Inspection opportunity is comparable after applying the supplied inspection-unit exposure.",
            "Signals identify investigation candidates and do not by themselves prove a special cause.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_ATTRIBUTE_SOURCE, NIST_POISSON_SOURCE),
    )


def c_chart(
    defects: Sequence[object], inspection_units: Sequence[object] | None = None
) -> ResultBundle:
    """Calculate a c chart for defect counts with equal inspection opportunity."""

    units = [1.0] * len(defects) if inspection_units is None else inspection_units
    return _poisson_attribute_chart(defects, units, chart="c")


def u_chart(
    defects: Sequence[object], inspection_units: Sequence[object]
) -> ResultBundle:
    """Calculate a u chart for defects per inspection unit."""

    return _poisson_attribute_chart(defects, inspection_units, chart="u")


def _append_rule_signal(
    signals: list[dict[str, object]],
    rule: str,
    start: int,
    end: int,
    side: str,
    involved: list[int],
) -> None:
    signals.append(
        {
            "rule": rule,
            "window_start": start,
            "window_end": end,
            "trigger_index": end,
            "side": side,
            "involved_indices": involved,
        }
    )


def western_electric_signals(
    values: Sequence[float], *, center: float, sigma: float
) -> list[dict[str, object]]:
    """Evaluate the four NIST WECO rules and two published trend rules."""

    observations = finite_values(values, "values")
    normalized_center = finite_values([center], "center")[0]
    normalized_sigma = finite_values([sigma], "sigma")[0]
    if normalized_sigma <= 0.0:
        return []

    signals: list[dict[str, object]] = []

    for index, value in enumerate(observations):
        if value > normalized_center + 3.0 * normalized_sigma:
            _append_rule_signal(signals, "WECO-1", index, index, "above", [index])
        elif value < normalized_center - 3.0 * normalized_sigma:
            _append_rule_signal(signals, "WECO-1", index, index, "below", [index])

    for end in range(2, len(observations)):
        start = end - 2
        window = observations[start : end + 1]
        above = [start + offset for offset, value in enumerate(window) if value > normalized_center + 2.0 * normalized_sigma]
        below = [start + offset for offset, value in enumerate(window) if value < normalized_center - 2.0 * normalized_sigma]
        if len(above) >= 2:
            _append_rule_signal(signals, "WECO-2", start, end, "above", above)
        if len(below) >= 2:
            _append_rule_signal(signals, "WECO-2", start, end, "below", below)

    for end in range(4, len(observations)):
        start = end - 4
        window = observations[start : end + 1]
        above = [start + offset for offset, value in enumerate(window) if value > normalized_center + normalized_sigma]
        below = [start + offset for offset, value in enumerate(window) if value < normalized_center - normalized_sigma]
        if len(above) >= 4:
            _append_rule_signal(signals, "WECO-3", start, end, "above", above)
        if len(below) >= 4:
            _append_rule_signal(signals, "WECO-3", start, end, "below", below)

    for end in range(7, len(observations)):
        start = end - 7
        window = observations[start : end + 1]
        if all(value > normalized_center for value in window):
            _append_rule_signal(signals, "WECO-4", start, end, "above", list(range(start, end + 1)))
        elif all(value < normalized_center for value in window):
            _append_rule_signal(signals, "WECO-4", start, end, "below", list(range(start, end + 1)))

    for end in range(5, len(observations)):
        start = end - 5
        window = observations[start : end + 1]
        if all(left < right for left, right in pairwise(window)):
            _append_rule_signal(signals, "TREND-6", start, end, "increasing", list(range(start, end + 1)))
        elif all(left > right for left, right in pairwise(window)):
            _append_rule_signal(signals, "TREND-6", start, end, "decreasing", list(range(start, end + 1)))

    for end in range(13, len(observations)):
        start = end - 13
        window = observations[start : end + 1]
        differences = [right - left for left, right in pairwise(window)]
        if all(
            current != 0.0 and following != 0.0 and current * following < 0.0
            for current, following in pairwise(differences)
        ):
            _append_rule_signal(signals, "ALTERNATING-14", start, end, "alternating", list(range(start, end + 1)))

    return signals


def nelson_signals(
    values: Sequence[float],
    *,
    center: float,
    sigma: float | None,
    enabled_rules: Sequence[int] = tuple(range(1, 9)),
    lower_limit: float | None = None,
    upper_limit: float | None = None,
) -> list[dict[str, object]]:
    """Evaluate the public eight-test special-cause rule set."""

    observations = finite_values(values, "values")
    normalized_center = finite_values([center], "center")[0]
    selected = tuple(dict.fromkeys(enabled_rules))
    if any(rule not in range(1, 9) for rule in selected):
        raise AnalysisInputError(
            "invalid_control_rule",
            "Enabled Nelson rules must be integers from 1 through 8.",
            "enabled_rules",
        )
    normalized_sigma = None if sigma is None else finite_values([sigma], "sigma")[0]
    needs_sigma = any(rule in {5, 6, 7, 8} for rule in selected) or (
        1 in selected and (lower_limit is None or upper_limit is None)
    )
    if needs_sigma and (normalized_sigma is None or normalized_sigma <= 0.0):
        return []
    normalized_lower = (
        normalized_center - 3.0 * normalized_sigma
        if lower_limit is None and normalized_sigma is not None
        else float("-inf")
        if lower_limit is None
        else finite_values([lower_limit], "lower_limit")[0]
    )
    normalized_upper = (
        normalized_center + 3.0 * normalized_sigma
        if upper_limit is None and normalized_sigma is not None
        else float("inf")
        if upper_limit is None
        else finite_values([upper_limit], "upper_limit")[0]
    )
    if normalized_lower >= normalized_upper:
        raise AnalysisInputError(
            "invalid_control_limits",
            "The lower control limit must be less than the upper control limit.",
            "lower_limit",
        )

    signals: list[dict[str, object]] = []
    if 1 in selected:
        for index, value in enumerate(observations):
            if value > normalized_upper:
                _append_rule_signal(signals, "NELSON-1", index, index, "above", [index])
            elif value < normalized_lower:
                _append_rule_signal(signals, "NELSON-1", index, index, "below", [index])

    if 2 in selected:
        for end in range(8, len(observations)):
            start = end - 8
            window = observations[start : end + 1]
            if all(value > normalized_center for value in window):
                _append_rule_signal(signals, "NELSON-2", start, end, "above", list(range(start, end + 1)))
            elif all(value < normalized_center for value in window):
                _append_rule_signal(signals, "NELSON-2", start, end, "below", list(range(start, end + 1)))

    if 3 in selected:
        for end in range(5, len(observations)):
            start = end - 5
            window = observations[start : end + 1]
            if all(left < right for left, right in pairwise(window)):
                _append_rule_signal(signals, "NELSON-3", start, end, "increasing", list(range(start, end + 1)))
            elif all(left > right for left, right in pairwise(window)):
                _append_rule_signal(signals, "NELSON-3", start, end, "decreasing", list(range(start, end + 1)))

    if 4 in selected:
        for end in range(13, len(observations)):
            start = end - 13
            window = observations[start : end + 1]
            differences = [right - left for left, right in pairwise(window)]
            if all(
                current != 0.0 and following != 0.0 and current * following < 0.0
                for current, following in pairwise(differences)
            ):
                _append_rule_signal(signals, "NELSON-4", start, end, "alternating", list(range(start, end + 1)))

    if 5 in selected and normalized_sigma is not None:
        for end in range(2, len(observations)):
            start = end - 2
            window = observations[start : end + 1]
            above = [start + offset for offset, value in enumerate(window) if value > normalized_center + 2.0 * normalized_sigma]
            below = [start + offset for offset, value in enumerate(window) if value < normalized_center - 2.0 * normalized_sigma]
            if len(above) >= 2:
                _append_rule_signal(signals, "NELSON-5", start, end, "above", above)
            if len(below) >= 2:
                _append_rule_signal(signals, "NELSON-5", start, end, "below", below)

    if 6 in selected and normalized_sigma is not None:
        for end in range(4, len(observations)):
            start = end - 4
            window = observations[start : end + 1]
            above = [start + offset for offset, value in enumerate(window) if value > normalized_center + normalized_sigma]
            below = [start + offset for offset, value in enumerate(window) if value < normalized_center - normalized_sigma]
            if len(above) >= 4:
                _append_rule_signal(signals, "NELSON-6", start, end, "above", above)
            if len(below) >= 4:
                _append_rule_signal(signals, "NELSON-6", start, end, "below", below)

    if 7 in selected and normalized_sigma is not None:
        for end in range(14, len(observations)):
            start = end - 14
            window = observations[start : end + 1]
            if all(abs(value - normalized_center) < normalized_sigma for value in window):
                _append_rule_signal(signals, "NELSON-7", start, end, "within", list(range(start, end + 1)))

    if 8 in selected and normalized_sigma is not None:
        for end in range(7, len(observations)):
            start = end - 7
            window = observations[start : end + 1]
            if all(abs(value - normalized_center) > normalized_sigma for value in window):
                above = any(value > normalized_center for value in window)
                below = any(value < normalized_center for value in window)
                side = "both" if above and below else "above" if above else "below"
                _append_rule_signal(signals, "NELSON-8", start, end, side, list(range(start, end + 1)))

    return signals


def individuals_moving_range(
    values: Sequence[float],
    *,
    target: float | None = None,
    rules: str = "western_electric",
) -> ResultBundle:
    """Calculate an Individuals and two-point Moving Range chart."""

    observations = finite_values(values, "values")
    if len(observations) < 2:
        raise AnalysisInputError(
            "insufficient_observations",
            "I-MR requires at least two finite observations.",
            "values",
        )
    if rules not in {"basic", "western_electric", "nelson"}:
        raise AnalysisInputError(
            "invalid_control_rule_set",
            "Rules must be 'basic', 'western_electric', or 'nelson'.",
            "rules",
        )

    center = fmean(observations) if target is None else finite_values([target], "target")[0]
    moving_ranges = [abs(current - previous) for previous, current in pairwise(observations)]
    average_moving_range = fmean(moving_ranges)
    estimated_sigma = average_moving_range / 1.128
    individuals_ucl = center + 3.0 * estimated_sigma
    individuals_lcl = center - 3.0 * estimated_sigma
    moving_range_ucl = average_moving_range * 3.267

    limit_signals = [
        index
        for index, value in enumerate(observations)
        if value > individuals_ucl or value < individuals_lcl
    ]
    if rules == "western_electric":
        rule_signals = western_electric_signals(
            observations, center=center, sigma=estimated_sigma
        )
    elif rules == "nelson":
        rule_signals = nelson_signals(
            observations, center=center, sigma=estimated_sigma
        )
    else:
        rule_signals = [
            {
                "rule": "WECO-1",
                "window_start": index,
                "window_end": index,
                "trigger_index": index,
                "side": "above" if observations[index] > center else "below",
                "involved_indices": [index],
            }
            for index in limit_signals
        ]
    individual_signals = sorted(
        {
            index
            for signal in rule_signals
            for index in signal["involved_indices"]
        }
    )
    moving_range_signals = [
        index + 1 for index, value in enumerate(moving_ranges) if value > moving_range_ucl
    ]
    warnings: list[str] = []
    if average_moving_range == 0.0:
        warnings.append("All consecutive observations are equal; estimated short-term variation is zero.")
    if rules == "western_electric":
        warnings.append(
            "WECO and trend rules increase sensitivity and false-alarm frequency; a signal requires investigation and is not proof of a special cause."
        )
    elif rules == "nelson":
        warnings.append(
            "Nelson tests 1-8 increase sensitivity and false-alarm frequency; select tests from process knowledge and investigate signals before acting."
        )

    provenance = (NIST_IMR_SOURCE,)
    if rules == "western_electric":
        provenance += (NIST_WECO_SOURCE,)
    elif rules == "nelson":
        provenance += (MINITAB_SPECIAL_CAUSE_SOURCE,)

    payload = {"values": observations, "target": target, "rules": rules}
    return ResultBundle(
        analysis_type="spc.imr",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={"moving_range_length": 2, "d2": 1.128, "d4": 3.267, "target": target, "rules": rules},
        tables={
            "observations": observations,
            "moving_ranges": moving_ranges,
            "limits": {
                "individuals": {"center": center, "lcl": individuals_lcl, "ucl": individuals_ucl},
                "moving_range": {"center": average_moving_range, "lcl": 0.0, "ucl": moving_range_ucl},
            },
        },
        plots={
            "individuals": {
                "values": observations,
                "signals": individual_signals,
                "rule_signals": rule_signals,
            },
            "moving_range": {"values": moving_ranges, "signals": moving_range_signals},
        },
        diagnostics={
            "individual_signal_indices": individual_signals,
            "individual_limit_signal_indices": limit_signals,
            "individual_rule_signals": rule_signals,
            "individual_rule_signal_count": len(rule_signals),
            "moving_range_signal_indices": moving_range_signals,
            "estimated_sigma": estimated_sigma,
        },
        assumptions=(
            "Observations are ordered in process time.",
            "Successive observations provide a meaningful estimate of short-term variation.",
            "Default limits use the two-point moving range and three-sigma convention.",
            "Supplementary rules are evaluated in observation order and mark investigation candidates, not confirmed special causes.",
        ),
        warnings=tuple(warnings),
        provenance=provenance,
    )


def xbar_r(
    subgroups: Sequence[Sequence[float]], *, rules: str = "basic"
) -> ResultBundle:
    """Calculate Xbar and R charts for equal-sized rational subgroups."""

    if len(subgroups) < 2:
        raise AnalysisInputError(
            "insufficient_subgroups",
            "Xbar-R requires at least two rational subgroups.",
            "subgroups",
        )
    if rules not in {"basic", "nelson"}:
        raise AnalysisInputError(
            "invalid_control_rule_set",
            "Xbar-R rules must be 'basic' or 'nelson'.",
            "rules",
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

    mean_limit_signals = [
        index for index, value in enumerate(subgroup_means) if value < xbar_lcl or value > xbar_ucl
    ]
    range_limit_signals = [
        index for index, value in enumerate(subgroup_ranges) if value < range_lcl or value > range_ucl
    ]
    if average_range == 0.0:
        xbar_rule_signals: list[dict[str, object]] = []
        range_rule_signals: list[dict[str, object]] = []
    else:
        xbar_rule_signals = nelson_signals(
            subgroup_means,
            center=grand_mean,
            sigma=a2 * average_range / 3.0,
            enabled_rules=(1,) if rules == "basic" else tuple(range(1, 9)),
            lower_limit=xbar_lcl,
            upper_limit=xbar_ucl,
        )
        range_rule_signals = nelson_signals(
            subgroup_ranges,
            center=average_range,
            sigma=None,
            enabled_rules=(1,) if rules == "basic" else (1, 2, 3, 4),
            lower_limit=range_lcl,
            upper_limit=range_ucl,
        )
    mean_signals = sorted(
        {
            index
            for signal in xbar_rule_signals
            for index in signal["involved_indices"]
        }
    )
    range_signals = sorted(
        {
            index
            for signal in range_rule_signals
            for index in signal["involved_indices"]
        }
    )
    warnings: list[str] = []
    if average_range == 0.0:
        warnings.append("Every subgroup has zero range; within-subgroup variation is zero.")
    if rules == "nelson":
        warnings.append(
            "Xbar uses Nelson tests 1-8 while R uses tests 1-4; additional tests increase sensitivity and false-alarm frequency."
        )

    payload = {"subgroups": normalized, "rules": rules}
    return ResultBundle(
        analysis_type="spc.xbar_r",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "subgroup_size": subgroup_size,
            "a2": a2,
            "d3": d3,
            "d4": d4,
            "rules": rules,
        },
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
            "xbar": {
                "values": subgroup_means,
                "signals": mean_signals,
                "rule_signals": xbar_rule_signals,
            },
            "range": {
                "values": subgroup_ranges,
                "signals": range_signals,
                "rule_signals": range_rule_signals,
            },
        },
        diagnostics={
            "xbar_signal_indices": mean_signals,
            "xbar_limit_signal_indices": mean_limit_signals,
            "xbar_rule_signals": xbar_rule_signals,
            "range_signal_indices": range_signals,
            "range_limit_signal_indices": range_limit_signals,
            "range_rule_signals": range_rule_signals,
        },
        assumptions=(
            "Subgroups are rational and ordered in process time.",
            "Subgroup sizes are constant and no larger than 10.",
            "The range is an appropriate estimator of within-subgroup variation.",
            "Supplementary rules mark investigation candidates and do not establish a special cause by themselves.",
        ),
        warnings=tuple(warnings),
        provenance=(
            (NIST_XBAR_R_SOURCE, MINITAB_SPECIAL_CAUSE_SOURCE)
            if rules == "nelson"
            else (NIST_XBAR_R_SOURCE,)
        ),
    )


def xbar_s(
    subgroups: Sequence[Sequence[float]], *, rules: str = "basic"
) -> ResultBundle:
    """Calculate Xbar and S charts for equal-sized rational subgroups."""

    if len(subgroups) < 2:
        raise AnalysisInputError(
            "insufficient_subgroups",
            "Xbar-S requires at least two rational subgroups.",
            "subgroups",
        )
    if rules not in {"basic", "nelson"}:
        raise AnalysisInputError(
            "invalid_control_rule_set",
            "Xbar-S rules must be 'basic' or 'nelson'.",
            "rules",
        )
    normalized = [
        finite_values(group, f"subgroups[{index}]")
        for index, group in enumerate(subgroups)
    ]
    subgroup_size = len(normalized[0])
    if not 2 <= subgroup_size <= 100:
        raise AnalysisInputError(
            "unsupported_subgroup_size",
            "Xbar-S supports constant subgroup sizes from 2 through 100.",
            "subgroups",
        )
    if any(len(group) != subgroup_size for group in normalized):
        raise AnalysisInputError(
            "unequal_subgroup_size",
            "Every rational subgroup must contain the same number of observations.",
            "subgroups",
        )

    subgroup_means = [fmean(group) for group in normalized]
    subgroup_standard_deviations = [stdev(group) for group in normalized]
    grand_mean = fmean(subgroup_means)
    average_standard_deviation = fmean(subgroup_standard_deviations)
    c4 = sqrt(2.0 / (subgroup_size - 1)) * exp(
        lgamma(subgroup_size / 2.0) - lgamma((subgroup_size - 1) / 2.0)
    )
    sigma_hat = average_standard_deviation / c4
    a3 = 3.0 / (c4 * sqrt(subgroup_size))
    spread_factor = 3.0 * sqrt(max(0.0, 1.0 - c4 * c4)) / c4
    b3 = max(0.0, 1.0 - spread_factor)
    b4 = 1.0 + spread_factor
    xbar_lcl = grand_mean - a3 * average_standard_deviation
    xbar_ucl = grand_mean + a3 * average_standard_deviation
    s_lcl = b3 * average_standard_deviation
    s_ucl = b4 * average_standard_deviation

    mean_limit_signals = [
        index
        for index, value in enumerate(subgroup_means)
        if value < xbar_lcl or value > xbar_ucl
    ]
    s_limit_signals = [
        index
        for index, value in enumerate(subgroup_standard_deviations)
        if value < s_lcl or value > s_ucl
    ]
    if average_standard_deviation == 0.0:
        xbar_rule_signals: list[dict[str, object]] = []
        s_rule_signals: list[dict[str, object]] = []
    else:
        xbar_rule_signals = nelson_signals(
            subgroup_means,
            center=grand_mean,
            sigma=sigma_hat / sqrt(subgroup_size),
            enabled_rules=(1,) if rules == "basic" else tuple(range(1, 9)),
            lower_limit=xbar_lcl,
            upper_limit=xbar_ucl,
        )
        s_rule_signals = nelson_signals(
            subgroup_standard_deviations,
            center=average_standard_deviation,
            sigma=None,
            enabled_rules=(1,) if rules == "basic" else (1, 2, 3, 4),
            lower_limit=s_lcl,
            upper_limit=s_ucl,
        )
    mean_signals = sorted(
        set(mean_limit_signals)
        | {index for signal in xbar_rule_signals for index in signal["involved_indices"]}
    )
    s_signals = sorted(
        set(s_limit_signals)
        | {index for signal in s_rule_signals for index in signal["involved_indices"]}
    )
    warnings: list[str] = []
    if subgroup_size < 9:
        warnings.append(
            "Subgroup sizes below 9 are usually monitored with Xbar-R; Xbar-S remains calculated from the public c4 formulas."
        )
    if average_standard_deviation == 0.0:
        warnings.append(
            "Every subgroup has zero standard deviation; within-subgroup variation is zero."
        )
    if rules == "nelson":
        warnings.append(
            "Xbar uses Nelson tests 1-8 while S uses tests 1-4; additional tests increase sensitivity and false-alarm frequency."
        )

    payload = {"subgroups": normalized, "rules": rules}
    return ResultBundle(
        analysis_type="spc.xbar_s",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "subgroup_size": subgroup_size,
            "c4": c4,
            "a3": a3,
            "b3": b3,
            "b4": b4,
            "rules": rules,
        },
        tables={
            "subgroups": normalized,
            "subgroup_means": subgroup_means,
            "subgroup_standard_deviations": subgroup_standard_deviations,
            "limits": {
                "xbar": {"center": grand_mean, "lcl": xbar_lcl, "ucl": xbar_ucl},
                "standard_deviation": {
                    "center": average_standard_deviation,
                    "lcl": s_lcl,
                    "ucl": s_ucl,
                },
            },
        },
        plots={
            "xbar": {
                "values": subgroup_means,
                "signals": mean_signals,
                "rule_signals": xbar_rule_signals,
            },
            "standard_deviation": {
                "values": subgroup_standard_deviations,
                "signals": s_signals,
                "rule_signals": s_rule_signals,
            },
        },
        diagnostics={
            "estimated_sigma": sigma_hat,
            "xbar_signal_indices": mean_signals,
            "xbar_limit_signal_indices": mean_limit_signals,
            "xbar_rule_signals": xbar_rule_signals,
            "standard_deviation_signal_indices": s_signals,
            "standard_deviation_limit_signal_indices": s_limit_signals,
            "standard_deviation_rule_signals": s_rule_signals,
        },
        assumptions=(
            "Subgroups are rational and ordered in process time.",
            "Subgroup sizes are constant.",
            "The average sample standard deviation divided by c4 estimates within-subgroup sigma.",
            "Three-sigma limits assume approximately normal within-subgroup observations.",
            "Supplementary rules mark investigation candidates and do not establish a special cause by themselves.",
        ),
        warnings=tuple(warnings),
        provenance=(
            (NIST_XBAR_S_SOURCE, MINITAB_XBAR_S_SOURCE, MINITAB_SPECIAL_CAUSE_SOURCE)
            if rules == "nelson"
            else (NIST_XBAR_S_SOURCE, MINITAB_XBAR_S_SOURCE)
        ),
    )
