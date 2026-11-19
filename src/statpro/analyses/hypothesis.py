"""Two-group inference with explicit assumptions and ResultBundle evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import fmean

from statpro.analyses.common import chi_square_survival, f_survival, finite_values
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_TWO_SAMPLE_T_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH Two-Sample t-Test",
    url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm",
)
NIST_CHI_SQUARE_SOURCE = ProvenanceSource(title="NIST/SEMATECH Chi-Square Test", url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35f.htm")
NIST_RANK_SUM_SOURCE = ProvenanceSource(title="NIST/SEMATECH Rank-Sum Tests", url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35a.htm")


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


def one_sample_t_test(values: Sequence[float], *, target: float, alpha: float = 0.05, variable_name: str = "Measurement") -> ResultBundle:
    """Two-sided one-sample t-test with a confidence interval for the process mean."""
    observations = finite_values(values, "values")
    name = variable_name.strip()
    if len(observations) < 2: raise AnalysisInputError("insufficient_observations", "At least two observations are required.", "values")
    if not name or not 0.001 <= alpha <= 0.5: raise AnalysisInputError("invalid_one_sample_input", "Use a variable name and valid alpha.", "alpha")
    mean = fmean(observations); variance = _sample_variance(observations, mean); standard_error = math.sqrt(variance / len(observations))
    if standard_error == 0.0: raise AnalysisInputError("zero_standard_error", "Within-sample variation is required for t inference.", "values")
    degrees = len(observations) - 1; difference = mean - target; t_value = difference / standard_error; p_value = _two_sided_t_probability(t_value, degrees); critical = _t_critical(alpha, degrees); lower, upper = mean - critical * standard_error, mean + critical * standard_error
    row = {"variable": name, "n": len(observations), "mean": mean, "target": target, "difference": difference, "standard_error": standard_error, "degrees_of_freedom": degrees, "t_value": t_value, "p_value": p_value, "confidence_interval_lower": lower, "confidence_interval_upper": upper, "significant": p_value <= alpha}
    return ResultBundle(analysis_type="hypothesis.one_sample_t", engine_version=ENGINE_VERSION, input_digest=input_digest({"values": observations, "target": target, "alpha": alpha, "variable_name": name}), parameters={"method": "one_sample_t", "alpha": alpha, "alternative": "two_sided", "target": target}, tables={"test": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics=row, assumptions=("Observations are independent and the response is continuous.", "For small samples, the population distribution should be approximately normal."), warnings=("Statistical significance does not establish practical significance; compare the confidence interval with the engineering tolerance.",), provenance=(NIST_TWO_SAMPLE_T_SOURCE,))


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


def mann_whitney_u_test(group_a: Sequence[float], group_b: Sequence[float], *, group_a_name: str = "Group A", group_b_name: str = "Group B", alpha: float = 0.05) -> ResultBundle:
    """Compare independent groups with average ranks and a tie-corrected normal approximation."""
    values_a, values_b = finite_values(group_a, "group_a"), finite_values(group_b, "group_b")
    names = (group_a_name.strip(), group_b_name.strip())
    if len(values_a) < 2 or len(values_b) < 2: raise AnalysisInputError("insufficient_observations", "Each independent group requires at least two observations.", "group_a")
    if not all(names) or names[0].casefold() == names[1].casefold(): raise AnalysisInputError("invalid_group_names", "Group names must be non-empty and distinct.", "group_a_name")
    if not 0.001 <= alpha <= 0.5: raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")
    pooled = sorted([(value, 0) for value in values_a] + [(value, 1) for value in values_b]); ranks = [0.0] * len(pooled); tie_sizes: list[int] = []; index = 0
    while index < len(pooled):
        end = index + 1
        while end < len(pooled) and pooled[end][0] == pooled[index][0]: end += 1
        for position in range(index, end): ranks[position] = (index + 1 + end) / 2.0
        tie_sizes.append(end - index); index = end
    n_a, n_b, total = len(values_a), len(values_b), len(pooled); rank_sum_a = sum(rank for rank, (_, group) in zip(ranks, pooled, strict=True) if group == 0)
    u_a = rank_sum_a - n_a * (n_a + 1) / 2.0; u_b = n_a * n_b - u_a; u = min(u_a, u_b); tie_adjustment = sum(size**3 - size for size in tie_sizes)
    variance = n_a * n_b / 12.0 * ((total + 1) - tie_adjustment / (total * (total - 1)))
    if variance <= 0.0: raise AnalysisInputError("zero_rank_variance", "All pooled values are tied; rank-sum inference is undefined.", "group_a")
    mean_u = n_a * n_b / 2.0; continuity = 0.5 if u > mean_u else -0.5 if u < mean_u else 0.0; z_value = (u - mean_u - continuity) / math.sqrt(variance); p_value = math.erfc(abs(z_value) / math.sqrt(2.0))
    row = {"u": u, "u_group_a": u_a, "u_group_b": u_b, "z_value": z_value, "p_value": p_value, "significant": p_value <= alpha}
    return ResultBundle(analysis_type="hypothesis.mann_whitney_u", engine_version=ENGINE_VERSION, input_digest=input_digest({"group_a": values_a, "group_b": values_b, "group_a_name": names[0], "group_b_name": names[1], "alpha": alpha}), parameters={"method": "mann_whitney_u_normal_approximation", "alpha": alpha, "group_a_name": names[0], "group_b_name": names[1], "tie_correction": True, "continuity_correction": True}, tables={"group_summary": {"columns": ["group", "n", "mean_rank"], "rows": [{"group": names[0], "n": n_a, "mean_rank": rank_sum_a / n_a}, {"group": names[1], "n": n_b, "mean_rank": (total * (total + 1) / 2.0 - rank_sum_a) / n_b}]}, "test": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics={**row, "rank_variance": variance, "reject_equal_distributions": p_value <= alpha}, assumptions=("Groups are independent and observations can be ranked.", "The normal approximation is more reliable with adequate samples; review small samples and ties."), warnings=("This is a two-sided, tie-corrected normal approximation; exact p-values are not calculated.",), provenance=(NIST_RANK_SUM_SOURCE,))


def wilcoxon_signed_rank_test(before: Sequence[float], after: Sequence[float], *, before_name: str = "Before", after_name: str = "After", alpha: float = 0.05) -> ResultBundle:
    """Compare paired values with signed ranks; zero differences are excluded."""
    values_before, values_after = finite_values(before, "before"), finite_values(after, "after")
    names = (before_name.strip(), after_name.strip())
    if len(values_before) < 2 or len(values_before) != len(values_after): raise AnalysisInputError("paired_length_mismatch", "Wilcoxon signed-rank requires equal-length groups with at least two pairs.", "before")
    if not all(names) or names[0].casefold() == names[1].casefold(): raise AnalysisInputError("invalid_group_names", "Measurement names must be non-empty and distinct.", "before_name")
    if not 0.001 <= alpha <= 0.5: raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")
    differences = [left - right for left, right in zip(values_before, values_after, strict=True)]; nonzero = [value for value in differences if value != 0.0]
    if len(nonzero) < 2: raise AnalysisInputError("insufficient_nonzero_differences", "At least two nonzero paired differences are required.", "before")
    ranked = sorted((abs(value), value) for value in nonzero); ranks = [0.0] * len(ranked); tie_sizes: list[int] = []; index = 0
    while index < len(ranked):
        end = index + 1
        while end < len(ranked) and ranked[end][0] == ranked[index][0]: end += 1
        for position in range(index, end): ranks[position] = (index + 1 + end) / 2.0
        tie_sizes.append(end - index); index = end
    w_plus = sum(rank for rank, (_, value) in zip(ranks, ranked, strict=True) if value > 0); w_minus = sum(rank for rank, (_, value) in zip(ranks, ranked, strict=True) if value < 0); n = len(nonzero); statistic = min(w_plus, w_minus)
    expected = n * (n + 1) / 4.0; variance = n * (n + 1) * (2 * n + 1) / 24.0 - sum(size**3 - size for size in tie_sizes) / 48.0
    if variance <= 0.0: raise AnalysisInputError("zero_rank_variance", "All nonzero absolute differences are tied; inference is undefined.", "before")
    continuity = 0.5 if statistic > expected else -0.5 if statistic < expected else 0.0; z_value = (statistic - expected - continuity) / math.sqrt(variance); p_value = math.erfc(abs(z_value) / math.sqrt(2.0)); row = {"w": statistic, "w_plus": w_plus, "w_minus": w_minus, "z_value": z_value, "p_value": p_value, "significant": p_value <= alpha}
    return ResultBundle(analysis_type="hypothesis.wilcoxon_signed_rank", engine_version=ENGINE_VERSION, input_digest=input_digest({"before": values_before, "after": values_after, "before_name": names[0], "after_name": names[1], "alpha": alpha}), parameters={"method": "wilcoxon_signed_rank_normal_approximation", "alpha": alpha, "before_name": names[0], "after_name": names[1], "zero_difference_count": len(differences) - n, "tie_correction": True, "continuity_correction": True}, tables={"test": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics={**row, "effective_pair_count": n, "rank_variance": variance, "reject_equal_locations": p_value <= alpha}, assumptions=("Each row is a paired measurement from the same unit.", "Paired differences are symmetrically distributed for location-shift interpretation."), warnings=("This is a two-sided, tie-corrected normal approximation; zero differences are excluded and exact p-values are not calculated.",), provenance=(NIST_RANK_SUM_SOURCE,))


def kruskal_wallis_test(groups: dict[str, Sequence[float]], *, alpha: float = 0.05) -> ResultBundle:
    """Compare three or more independent groups using tie-corrected pooled ranks."""
    if len(groups) < 3 or not 0.001 <= alpha <= 0.5: raise AnalysisInputError("invalid_kruskal_wallis_input", "Kruskal-Wallis needs three or more groups and valid alpha.", "groups")
    normalized = {name.strip(): finite_values(values, f"groups.{name}") for name, values in groups.items()}
    if any(not name or len(values) < 2 for name, values in normalized.items()) or len(normalized) != len(groups): raise AnalysisInputError("insufficient_observations", "Each group needs a unique non-empty name and at least two observations.", "groups")
    pooled = sorted((value, name) for name, values in normalized.items() for value in values); ranks = [0.0] * len(pooled); ties: list[int] = []; index = 0
    while index < len(pooled):
        end = index + 1
        while end < len(pooled) and pooled[end][0] == pooled[index][0]: end += 1
        for position in range(index, end): ranks[position] = (index + 1 + end) / 2.0
        ties.append(end - index); index = end
    total = len(pooled); rank_sums = {name: sum(rank for rank, (_, owner) in zip(ranks, pooled, strict=True) if owner == name) for name in normalized}; raw_h = 12.0 / (total * (total + 1)) * sum(rank_sums[name] ** 2 / len(values) for name, values in normalized.items()) - 3 * (total + 1); correction = 1.0 - sum(size**3 - size for size in ties) / (total**3 - total)
    if correction <= 0.0: raise AnalysisInputError("zero_rank_variance", "All pooled values are tied; rank comparison is undefined.", "groups")
    h_value = raw_h / correction; degrees = len(normalized) - 1; p_value = chi_square_survival(h_value, degrees); row = {"h_value": h_value, "degrees_of_freedom": degrees, "p_value": p_value, "significant": p_value <= alpha}
    summary = [{"group": name, "n": len(values), "mean_rank": rank_sums[name] / len(values)} for name, values in normalized.items()]
    return ResultBundle(analysis_type="hypothesis.kruskal_wallis", engine_version=ENGINE_VERSION, input_digest=input_digest({"groups": normalized, "alpha": alpha}), parameters={"method": "kruskal_wallis_tie_corrected", "alpha": alpha, "tie_correction": correction}, tables={"group_summary": {"columns": ["group", "n", "mean_rank"], "rows": summary}, "test": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics={**row, "tie_correction": correction, "reject_equal_distributions": p_value <= alpha if p_value is not None else False}, assumptions=("Groups are independent and observations can be ranked.",), warnings=("A significant omnibus result does not identify which groups differ; apply a separately validated post-hoc comparison.",), provenance=(NIST_RANK_SUM_SOURCE,))


def independent_tost_equivalence(group_a: Sequence[float], group_b: Sequence[float], *, lower_margin: float, upper_margin: float, group_a_name: str = "Group A", group_b_name: str = "Group B", alpha: float = 0.05) -> ResultBundle:
    """Welch two one-sided tests for a pre-specified mean-difference equivalence interval."""
    values_a, values_b = finite_values(group_a, "group_a"), finite_values(group_b, "group_b")
    names = (group_a_name.strip(), group_b_name.strip())
    if len(values_a) < 2 or len(values_b) < 2: raise AnalysisInputError("insufficient_observations", "Each group requires at least two observations.", "group_a")
    if not all(names) or names[0].casefold() == names[1].casefold(): raise AnalysisInputError("invalid_group_names", "Group names must be non-empty and distinct.", "group_a_name")
    if not 0.001 <= alpha <= 0.5 or not lower_margin < upper_margin: raise AnalysisInputError("invalid_equivalence_bounds", "Use valid alpha and lower margin strictly below upper margin.", "lower_margin")
    mean_a, mean_b = fmean(values_a), fmean(values_b); variance_a, variance_b = _sample_variance(values_a, mean_a), _sample_variance(values_b, mean_b); terms = variance_a / len(values_a), variance_b / len(values_b); standard_error = math.sqrt(sum(terms))
    if standard_error == 0.0: raise AnalysisInputError("zero_standard_error", "Within-group variation is required for TOST inference.", "group_a")
    degrees = sum(terms) ** 2 / (terms[0] ** 2 / (len(values_a) - 1) + terms[1] ** 2 / (len(values_b) - 1)); difference = mean_a - mean_b
    def upper_tail(t_value: float) -> float:
        two_sided = _two_sided_t_probability(t_value, degrees)
        return two_sided / 2.0 if t_value >= 0 else 1.0 - two_sided / 2.0
    lower_t, upper_t = (difference - lower_margin) / standard_error, (difference - upper_margin) / standard_error
    lower_p, upper_p = upper_tail(lower_t), 1.0 - upper_tail(upper_t); critical = _t_critical(2 * alpha, degrees); ci_lower, ci_upper = difference - critical * standard_error, difference + critical * standard_error; equivalent = lower_p <= alpha and upper_p <= alpha
    row = {"difference": difference, "lower_margin": lower_margin, "upper_margin": upper_margin, "lower_t": lower_t, "lower_p_value": lower_p, "upper_t": upper_t, "upper_p_value": upper_p, "confidence_interval_lower": ci_lower, "confidence_interval_upper": ci_upper, "equivalent": equivalent}
    return ResultBundle(analysis_type="hypothesis.independent_tost_equivalence", engine_version=ENGINE_VERSION, input_digest=input_digest({"group_a": values_a, "group_b": values_b, "lower_margin": lower_margin, "upper_margin": upper_margin, "group_a_name": names[0], "group_b_name": names[1], "alpha": alpha}), parameters={"method": "welch_tost", "alpha": alpha, "confidence_level": 1 - 2 * alpha, "group_a_name": names[0], "group_b_name": names[1]}, tables={"test": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics={**row, "degrees_of_freedom": degrees, "standard_error": standard_error}, assumptions=("Groups are independent and observations are continuous.", "Equivalence margins were defined before examining the data."), warnings=("Failure to reject a difference test does not establish equivalence; interpret both one-sided tests and the confidence interval.",), provenance=(NIST_TWO_SAMPLE_T_SOURCE,))


def one_way_anova(groups: dict[str, Sequence[float]], *, alpha: float = 0.05) -> ResultBundle:
    if len(groups) < 2 or not 0.001 <= alpha <= 0.5: raise AnalysisInputError("invalid_anova_input", "ANOVA needs two or more groups and valid alpha.", "groups")
    normalized = {name: finite_values(values, f"groups.{name}") for name, values in groups.items()}
    if any(not name.strip() or len(values) < 2 for name, values in normalized.items()): raise AnalysisInputError("insufficient_observations", "Each group needs a name and at least two observations.", "groups")
    all_values = [value for values in normalized.values() for value in values]; grand = fmean(all_values); means = {name: fmean(values) for name, values in normalized.items()}; between = sum(len(normalized[name]) * (mean-grand)**2 for name, mean in means.items()); within = sum(sum((value-means[name])**2 for value in values) for name, values in normalized.items()); dfb, dfw = len(normalized)-1, len(all_values)-len(normalized); msb, msw = between/dfb, within/dfw; statistic = msb/msw if msw else None; p = f_survival(statistic, dfb, dfw); eta = between/(between+within) if between+within else None
    return ResultBundle(analysis_type="hypothesis.one_way_anova", engine_version=ENGINE_VERSION, input_digest=input_digest({"groups": normalized,"alpha":alpha}), parameters={"method":"one_way_anova","alpha":alpha}, tables={"anova":{"columns":["source","df","sum_squares","mean_square","f_value","p_value"],"rows":[{"source":"Between groups","df":dfb,"sum_squares":between,"mean_square":msb,"f_value":statistic,"p_value":p},{"source":"Within groups","df":dfw,"sum_squares":within,"mean_square":msw,"f_value":None,"p_value":None}]},"group_summary":{"columns":["group","n","mean"],"rows":[{"group":name,"n":len(values),"mean":means[name]} for name,values in normalized.items()]}},plots={},diagnostics={"f_statistic":statistic,"p_value":p,"eta_squared":eta,"reject_equal_means":p <= alpha if p is not None else False},assumptions=("Groups are independent with approximately equal within-group variance.",),warnings=("A significant omnibus ANOVA does not identify which groups differ; use a separately validated post-hoc method.",),provenance=(NIST_TWO_SAMPLE_T_SOURCE,))


def chi_square_independence(rows: Sequence[str], columns: Sequence[str], counts: Sequence[Sequence[int]], *, alpha: float = 0.05) -> ResultBundle:
    if len(rows) < 2 or len(columns) < 2 or len(counts) != len(rows) or any(len(row) != len(columns) for row in counts): raise AnalysisInputError("invalid_contingency_table", "A contingency table needs at least two rows and two columns.", "counts")
    if not 0.001 <= alpha <= 0.5 or any(not name.strip() for name in [*rows, *columns]): raise AnalysisInputError("invalid_chi_square_input", "Use non-empty category names and a valid alpha.", "alpha")
    values = [[float(value) for value in row] for row in counts]
    if any(value < 0 or not value.is_integer() for row in values for value in row): raise AnalysisInputError("invalid_count", "Contingency values must be non-negative whole counts.", "counts")
    total = sum(sum(row) for row in values)
    row_totals, col_totals = [sum(row) for row in values], [sum(values[i][j] for i in range(len(rows))) for j in range(len(columns))]
    if total <= 0 or any(value == 0 for value in [*row_totals, *col_totals]): raise AnalysisInputError("empty_category", "Each row and column needs an observation.", "counts")
    expected = [[row_totals[i] * col_totals[j] / total for j in range(len(columns))] for i in range(len(rows))]
    statistic = sum((values[i][j] - expected[i][j]) ** 2 / expected[i][j] for i in range(len(rows)) for j in range(len(columns))); df = (len(rows)-1)*(len(columns)-1); p_value = chi_square_survival(statistic, df)
    cells = [{"row": rows[i], "column": columns[j], "observed": int(values[i][j]), "expected": expected[i][j]} for i in range(len(rows)) for j in range(len(columns))]
    warnings = ("Some expected counts are below 5; review the asymptotic approximation.",) if any(value < 5 for row in expected for value in row) else ()
    return ResultBundle(analysis_type="hypothesis.chi_square_independence", engine_version=ENGINE_VERSION, input_digest=input_digest({"rows":list(rows),"columns":list(columns),"counts":values,"alpha":alpha}), parameters={"method":"chi_square_independence","alpha":alpha}, tables={"cells":{"columns":["row","column","observed","expected"],"rows":cells}}, plots={}, diagnostics={"chi_square":statistic,"degrees_of_freedom":df,"p_value":p_value,"cramers_v":math.sqrt(statistic/(total*min(len(rows)-1,len(columns)-1))),"reject_independence":p_value <= alpha if p_value is not None else False}, assumptions=("Observations are independent and appear in one table cell.", "Expected counts require review."), warnings=warnings, provenance=(NIST_CHI_SQUARE_SOURCE,))
