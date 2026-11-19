"""Univariate descriptive statistics with explicit result provenance."""

from __future__ import annotations

import math
from statistics import fmean, median, stdev
from collections.abc import Sequence

from statpro.analyses.common import finite_values
from statpro.analyses.hypothesis import _t_critical
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_DESCRIPTIVE_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH Exploratory Data Analysis",
    url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm",
)


def _linear_quantile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    return sorted_values[lower] + (position - lower) * (sorted_values[upper] - sorted_values[lower])


def descriptive_statistics(values: Sequence[float], *, variable_name: str = "Measurement", alpha: float = 0.05) -> ResultBundle:
    """Summarize one continuous measurement column and its mean confidence interval."""
    observations = finite_values(values, "values")
    if len(observations) < 2:
        raise AnalysisInputError("insufficient_observations", "Descriptive statistics need at least two observations.", "values")
    if not 0.001 <= alpha <= 0.5:
        raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")
    name = variable_name.strip()
    if not name:
        raise AnalysisInputError("invalid_variable_name", "Variable name must not be empty.", "variable_name")
    ordered = sorted(observations)
    count = len(observations)
    mean = fmean(observations)
    sample_standard_deviation = stdev(observations)
    standard_error = sample_standard_deviation / math.sqrt(count)
    critical = _t_critical(alpha, count - 1)
    lower, upper = mean - critical * standard_error, mean + critical * standard_error
    second = sum((value - mean) ** 2 for value in observations) / count
    third = sum((value - mean) ** 3 for value in observations) / count
    fourth = sum((value - mean) ** 4 for value in observations) / count
    skewness = third / second ** 1.5 if second else 0.0
    excess_kurtosis = fourth / second ** 2 - 3.0 if second else 0.0
    q1, q3 = _linear_quantile(ordered, 0.25), _linear_quantile(ordered, 0.75)
    summary = {
        "variable": name, "n": count, "mean": mean, "standard_deviation": sample_standard_deviation,
        "standard_error": standard_error, "mean_confidence_interval_lower": lower,
        "mean_confidence_interval_upper": upper, "minimum": ordered[0], "q1": q1,
        "median": median(ordered), "q3": q3, "maximum": ordered[-1], "range": ordered[-1] - ordered[0],
        "interquartile_range": q3 - q1, "coefficient_of_variation": sample_standard_deviation / mean if mean != 0 else None,
        "skewness": skewness, "excess_kurtosis": excess_kurtosis,
    }
    return ResultBundle(
        analysis_type="descriptive.univariate",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest({"values": observations, "variable_name": name, "alpha": alpha}),
        parameters={"variable_name": name, "alpha": alpha, "confidence_level": 1 - alpha, "quantile_method": "linear_interpolation"},
        tables={"summary": {"columns": list(summary), "rows": [summary]}},
        plots={},
        diagnostics={"count": count, "mean": mean, "standard_deviation": sample_standard_deviation, "mean_confidence_interval_lower": lower, "mean_confidence_interval_upper": upper},
        assumptions=("Observations are numeric measurements from a clearly defined population or process.", "The mean confidence interval uses a two-sided Student t critical value."),
        warnings=("Descriptive statistics summarize the supplied observations; they do not establish process stability, normality, or causation.",),
        provenance=(NIST_DESCRIPTIVE_SOURCE,),
    )
