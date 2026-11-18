"""Two-group inference with explicit assumptions and ResultBundle evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import fmean

from statpro.analyses.common import f_survival, finite_values
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_TWO_SAMPLE_T_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH Two-Sample t-Test",
    url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm",
)


def _sample_variance(values: list[float], mean: float) -> float:
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


def _two_sided_t_probability(statistic: float, degrees_of_freedom: float) -> float:
    return f_survival(statistic * statistic, 1.0, degrees_of_freedom) or 0.0


def _t_critical(alpha: float, degrees_of_freedom: float) -> float:
    lower, upper = 0.0, 1.0
    while _two_sided_t_probability(upper, degrees_of_freedom) > alpha:
        upper *= 2.0
        if upper > 1e6:
            raise AnalysisInputError("distribution_not_converged", "t critical-value search exceeded its bound.", "alpha")
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if _two_sided_t_probability(midpoint, degrees_of_freedom) > alpha:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def independent_welch_t_test(
    group_a: Sequence[float], group_b: Sequence[float], *, group_a_name: str = "Group A", group_b_name: str = "Group B", alpha: float = 0.05
) -> ResultBundle:
    """Compare two independent continuous groups without pooling variances."""
    values_a, values_b = finite_values(group_a, "group_a"), finite_values(group_b, "group_b")
    if len(values_a) < 2 or len(values_b) < 2:
        raise AnalysisInputError("insufficient_observations", "Each independent group requires at least two observations.", "group_a")
    if not 0.001 <= alpha <= 0.5:
        raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")
    names = (group_a_name.strip(), group_b_name.strip())
    if not all(names) or names[0].casefold() == names[1].casefold():
        raise AnalysisInputError("invalid_group_names", "Group names must be non-empty and distinct.", "group_a_name")
    mean_a, mean_b = fmean(values_a), fmean(values_b)
    variance_a, variance_b = _sample_variance(values_a, mean_a), _sample_variance(values_b, mean_b)
    variance_terms = variance_a / len(values_a), variance_b / len(values_b)
    standard_error = math.sqrt(sum(variance_terms))
    if standard_error == 0.0:
        raise AnalysisInputError("zero_standard_error", "Both groups have zero within-group variation; Welch t inference is undefined.", "group_a")
    degrees_of_freedom = sum(variance_terms) ** 2 / (variance_terms[0] ** 2 / (len(values_a) - 1) + variance_terms[1] ** 2 / (len(values_b) - 1))
    difference = mean_a - mean_b
    t_statistic = difference / standard_error
    p_value = _two_sided_t_probability(t_statistic, degrees_of_freedom)
    critical = _t_critical(alpha, degrees_of_freedom)
    interval = (difference - critical * standard_error, difference + critical * standard_error)
    return ResultBundle(
        analysis_type="hypothesis.independent_welch_t",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest({"group_a": values_a, "group_b": values_b, "group_a_name": names[0], "group_b_name": names[1], "alpha": alpha}),
        parameters={"method": "welch_two_sample_t", "alpha": alpha, "group_a_name": names[0], "group_b_name": names[1], "alternative": "two_sided"},
        tables={"group_summary": {"columns": ["group", "n", "mean", "sample_variance"], "rows": [{"group": names[0], "n": len(values_a), "mean": mean_a, "sample_variance": variance_a}, {"group": names[1], "n": len(values_b), "mean": mean_b, "sample_variance": variance_b}]}, "test": {"columns": ["difference", "standard_error", "degrees_of_freedom", "t_statistic", "p_value", "confidence_interval_lower", "confidence_interval_upper", "significant"], "rows": [{"difference": difference, "standard_error": standard_error, "degrees_of_freedom": degrees_of_freedom, "t_statistic": t_statistic, "p_value": p_value, "confidence_interval_lower": interval[0], "confidence_interval_upper": interval[1], "significant": p_value <= alpha}]}},
        plots={},
        diagnostics={"difference": difference, "standard_error": standard_error, "degrees_of_freedom": degrees_of_freedom, "t_statistic": t_statistic, "p_value": p_value, "confidence_interval_lower": interval[0], "confidence_interval_upper": interval[1], "reject_equal_means": p_value <= alpha},
        assumptions=("Groups are independent and each observation belongs to exactly one group.", "The response is continuous; Welch inference does not pool variances.", "Small samples require engineering review of distribution shape and outliers."),
        warnings=("This test does not establish practical significance; review the confidence interval against the engineering decision threshold.",),
        provenance=(NIST_TWO_SAMPLE_T_SOURCE,),
    )


def paired_t_test(before: Sequence[float], after: Sequence[float], *, before_name: str = "Before", after_name: str = "After", alpha: float = 0.05) -> ResultBundle:
    """Compare aligned paired measurements through their within-pair differences."""
    values_before, values_after = finite_values(before, "before"), finite_values(after, "after")
    if len(values_before) < 2 or len(values_before) != len(values_after):
        raise AnalysisInputError("paired_length_mismatch", "Paired t-test requires equal-length groups with at least two pairs.", "before")
    if not 0.001 <= alpha <= 0.5:
        raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")
    differences = [left - right for left, right in zip(values_before, values_after, strict=True)]
    mean_difference = fmean(differences); variance = _sample_variance(differences, mean_difference)
    standard_error = math.sqrt(variance / len(differences))
    if standard_error == 0.0:
        raise AnalysisInputError("zero_standard_error", "Pair differences have zero variation; t inference is undefined.", "before")
    degrees_of_freedom = len(differences) - 1; statistic = mean_difference / standard_error; p_value = _two_sided_t_probability(statistic, degrees_of_freedom); critical = _t_critical(alpha, degrees_of_freedom)
    lower, upper = mean_difference - critical * standard_error, mean_difference + critical * standard_error
    return ResultBundle(analysis_type="hypothesis.paired_t", engine_version=ENGINE_VERSION, input_digest=input_digest({"before": values_before, "after": values_after, "before_name": before_name, "after_name": after_name, "alpha": alpha}), parameters={"method": "paired_t", "alpha": alpha, "before_name": before_name, "after_name": after_name, "pair_count": len(differences), "alternative": "two_sided"}, tables={"test": {"columns": ["difference", "standard_error", "degrees_of_freedom", "t_statistic", "p_value", "confidence_interval_lower", "confidence_interval_upper", "significant"], "rows": [{"difference": mean_difference, "standard_error": standard_error, "degrees_of_freedom": degrees_of_freedom, "t_statistic": statistic, "p_value": p_value, "confidence_interval_lower": lower, "confidence_interval_upper": upper, "significant": p_value <= alpha}]}}, plots={}, diagnostics={"difference": mean_difference, "standard_error": standard_error, "degrees_of_freedom": degrees_of_freedom, "t_statistic": statistic, "p_value": p_value, "confidence_interval_lower": lower, "confidence_interval_upper": upper, "reject_equal_means": p_value <= alpha}, assumptions=("Each before/after row is the same matched unit.", "Pair differences are independent and approximately normal for small samples."), warnings=("This test evaluates paired mean difference, not practical significance.",), provenance=(NIST_TWO_SAMPLE_T_SOURCE,))
