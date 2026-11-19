"""Prospective balanced sample-size planning."""
from __future__ import annotations
import math
from statpro.analyses.common import _regularized_beta
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_POWER_SOURCE = ProvenanceSource(title="NIST/SEMATECH Sample Size and Power", url="https://www.itl.nist.gov/div898/handbook/prc/section2/prc222.htm")
NIST_ANOVA_SOURCE = ProvenanceSource(title="NIST/SEMATECH One-Way ANOVA", url="https://www.itl.nist.gov/div898/handbook/prc/section4/prc433.htm")
PWR_ANOVA_SOURCE = ProvenanceSource(title="R pwr one-way ANOVA power calculation", url="https://search.r-project.org/CRAN/refmans/pwr/html/pwr.anova.test.html")

def _normal_quantile(probability: float) -> float:
    if not 0.0 < probability < 1.0: raise AnalysisInputError("invalid_probability", "Probability must be strictly between zero and one.", "probability")
    low, high = -10.0, 10.0
    for _ in range(100):
        mid = (low + high) / 2.0
        if 0.5 * math.erfc(-mid / math.sqrt(2.0)) < probability: low = mid
        else: high = mid
    return (low + high) / 2.0


def _f_quantile(probability: float, numerator_df: int, denominator_df: int) -> float:
    low, high = 0.0, 1.0
    def cdf(value: float) -> float:
        transformed = numerator_df * value / (numerator_df * value + denominator_df)
        return _regularized_beta(transformed, numerator_df / 2.0, denominator_df / 2.0)
    while cdf(high) < probability:
        high *= 2.0
        if high > 1e12:
            raise AnalysisInputError("distribution_not_converged", "The F critical value search exceeded its bound.", "distribution")
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if cdf(midpoint) < probability: low = midpoint
        else: high = midpoint
    return (low + high) / 2.0


def _noncentral_f_cdf(value: float, numerator_df: int, denominator_df: int, noncentrality: float) -> float:
    transformed = numerator_df * value / (numerator_df * value + denominator_df)
    poisson_mean = noncentrality / 2.0
    if poisson_mean == 0.0:
        return _regularized_beta(transformed, numerator_df / 2.0, denominator_df / 2.0)
    mode = int(poisson_mean)
    mode_weight = math.exp(-poisson_mean + mode * math.log(poisson_mean) - math.lgamma(mode + 1.0))
    total = mode_weight * _regularized_beta(transformed, numerator_df / 2.0 + mode, denominator_df / 2.0)
    mass = mode_weight
    lower_index = upper_index = mode
    lower_weight = upper_weight = mode_weight
    for _ in range(100_000):
        if lower_index > 0:
            lower_weight *= lower_index / poisson_mean
            lower_index -= 1
            mass += lower_weight
            total += lower_weight * _regularized_beta(transformed, numerator_df / 2.0 + lower_index, denominator_df / 2.0)
        upper_index += 1
        upper_weight *= poisson_mean / upper_index
        mass += upper_weight
        total += upper_weight * _regularized_beta(transformed, numerator_df / 2.0 + upper_index, denominator_df / 2.0)
        if 1.0 - mass <= 1e-12:
            return min(1.0, max(0.0, total))
    raise AnalysisInputError("distribution_not_converged", "The noncentral F probability calculation did not converge.", "distribution")


def _one_way_anova_power(group_count: int, sample_size_per_group: int, effect_size: float, alpha: float) -> tuple[float, float]:
    numerator_df = group_count - 1
    denominator_df = group_count * (sample_size_per_group - 1)
    critical_value = _f_quantile(1.0 - alpha, numerator_df, denominator_df)
    noncentrality = group_count * sample_size_per_group * effect_size**2
    power = 1.0 - _noncentral_f_cdf(critical_value, numerator_df, denominator_df, noncentrality)
    return power, critical_value


def one_way_anova_sample_size(*, group_count: int, effect_size: float, alpha: float = 0.05, target_power: float = 0.8) -> ResultBundle:
    """Plan equal group sizes for a fixed-effects one-way omnibus ANOVA."""
    if not 3 <= group_count <= 100:
        raise AnalysisInputError("invalid_group_count", "Use between 3 and 100 groups for multi-group ANOVA planning.", "group_count")
    if not 0.0 < effect_size <= 10.0:
        raise AnalysisInputError("invalid_effect_size", "Cohen's f must be greater than zero and no more than 10.", "effect_size")
    if not 0.001 <= alpha <= 0.5 or not 0.5 < target_power < 0.999:
        raise AnalysisInputError("invalid_power_inputs", "Use valid alpha and target power above 0.5.", "target_power")
    lower = upper = 2
    achieved_power, critical_value = _one_way_anova_power(group_count, upper, effect_size, alpha)
    while achieved_power < target_power:
        lower = upper + 1
        upper *= 2
        if upper > 1_000_000:
            raise AnalysisInputError("sample_size_limit_exceeded", "The requested ANOVA design needs more than 1,000,000 observations per group.", "effect_size")
        achieved_power, critical_value = _one_way_anova_power(group_count, upper, effect_size, alpha)
    while lower < upper:
        midpoint = (lower + upper) // 2
        midpoint_power, _ = _one_way_anova_power(group_count, midpoint, effect_size, alpha)
        if midpoint_power >= target_power: upper = midpoint
        else: lower = midpoint + 1
    sample_size_per_group = upper
    achieved_power, critical_value = _one_way_anova_power(group_count, sample_size_per_group, effect_size, alpha)
    total_sample_size = group_count * sample_size_per_group
    row = {"group_count": group_count, "effect_size": effect_size, "alpha": alpha, "target_power": target_power, "sample_size_per_group": sample_size_per_group, "total_sample_size": total_sample_size, "achieved_power": achieved_power, "numerator_degrees_of_freedom": group_count - 1, "denominator_degrees_of_freedom": total_sample_size - group_count, "noncentrality": total_sample_size * effect_size**2, "critical_value": critical_value}
    return ResultBundle(analysis_type="power.one_way_anova", engine_version=ENGINE_VERSION, input_digest=input_digest(row), parameters={"method": "noncentral_f_balanced_fixed_effects_one_way_anova", "effect_size": "cohen_f", "alternative": "omnibus"}, tables={"plan": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics=row, assumptions=("Groups are fixed, independent, and planned with equal sample sizes.", "Within-group observations are approximately normal with a common variance.", "Cohen's f is specified prospectively for the omnibus difference among group means."), warnings=("This is a prospective planning calculation, not a post-hoc observed-power interpretation.", "The omnibus design does not plan power for a specific pairwise or multiple-comparison procedure; add attrition separately."), provenance=(NIST_ANOVA_SOURCE, PWR_ANOVA_SOURCE))

def two_sample_mean_sample_size(*, difference: float, standard_deviation: float, alpha: float = 0.05, target_power: float = 0.8) -> ResultBundle:
    """Estimate equal group sample size using a normal approximation for a two-sided two-sample mean test."""
    if difference <= 0 or standard_deviation <= 0: raise AnalysisInputError("invalid_effect_inputs", "Difference and standard deviation must be positive.", "difference")
    if not 0.001 <= alpha <= 0.5 or not 0.5 < target_power < 0.999: raise AnalysisInputError("invalid_power_inputs", "Use valid alpha and target power above 0.5.", "target_power")
    effect_size = difference / standard_deviation; z_alpha = _normal_quantile(1 - alpha / 2); z_power = _normal_quantile(target_power); per_group = math.ceil(2 * ((z_alpha + z_power) / effect_size) ** 2); total = 2 * per_group
    row = {"difference": difference, "standard_deviation": standard_deviation, "effect_size": effect_size, "alpha": alpha, "target_power": target_power, "sample_size_per_group": per_group, "total_sample_size": total}
    return ResultBundle(analysis_type="power.two_sample_mean", engine_version=ENGINE_VERSION, input_digest=input_digest(row), parameters={"method": "normal_approximation_balanced_two_sample", "alternative": "two_sided"}, tables={"plan": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics=row, assumptions=("Two independent groups have equal planned sizes and a common planning standard deviation.", "Normal approximation is used; refine for small samples or complex designs."), warnings=("This is a planning calculation, not a post-hoc observed-power interpretation.",), provenance=(NIST_POWER_SOURCE,))


def two_sample_proportion_sample_size(*, proportion_a: float, proportion_b: float, alpha: float = 0.05, target_power: float = 0.8) -> ResultBundle:
    """Estimate equal group sample size for a two-sided independent proportion comparison."""
    if not 0.0 <= proportion_a <= 1.0 or not 0.0 <= proportion_b <= 1.0 or proportion_a == proportion_b:
        raise AnalysisInputError("invalid_proportion_effect", "Use two different expected proportions between zero and one.", "proportion_a")
    if not 0.001 <= alpha <= 0.5 or not 0.5 < target_power < 0.999:
        raise AnalysisInputError("invalid_power_inputs", "Use valid alpha and target power above 0.5.", "target_power")
    pooled = (proportion_a + proportion_b) / 2.0
    z_alpha = _normal_quantile(1 - alpha / 2.0)
    z_power = _normal_quantile(target_power)
    numerator = z_alpha * math.sqrt(2.0 * pooled * (1.0 - pooled)) + z_power * math.sqrt(proportion_a * (1.0 - proportion_a) + proportion_b * (1.0 - proportion_b))
    difference = abs(proportion_a - proportion_b)
    per_group = math.ceil((numerator / difference) ** 2)
    row = {"proportion_a": proportion_a, "proportion_b": proportion_b, "absolute_difference": difference, "alpha": alpha, "target_power": target_power, "sample_size_per_group": per_group, "total_sample_size": 2 * per_group}
    return ResultBundle(analysis_type="power.two_sample_proportion", engine_version=ENGINE_VERSION, input_digest=input_digest(row), parameters={"method": "normal_approximation_balanced_two_proportion", "alternative": "two_sided"}, tables={"plan": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics=row, assumptions=("Groups are independent with equal planned sample sizes.", "Expected defect outcomes follow a binomial model and the normal approximation is adequate for planning."), warnings=("This is a prospective planning calculation; assess rare-defect and continuity-correction needs before finalizing the protocol.",), provenance=(NIST_POWER_SOURCE,))


def one_sample_proportion_sample_size(*, null_proportion: float, expected_proportion: float, alpha: float = 0.05, target_power: float = 0.8) -> ResultBundle:
    """Estimate required observations for a two-sided one-sample proportion test."""
    if not 0.0 < null_proportion < 1.0 or not 0.0 < expected_proportion < 1.0 or null_proportion == expected_proportion:
        raise AnalysisInputError("invalid_proportion_effect", "Use two different proportions strictly between zero and one.", "null_proportion")
    if not 0.001 <= alpha <= 0.5 or not 0.5 < target_power < 0.999:
        raise AnalysisInputError("invalid_power_inputs", "Use valid alpha and target power above 0.5.", "target_power")
    z_alpha = _normal_quantile(1 - alpha / 2.0)
    z_power = _normal_quantile(target_power)
    difference = abs(expected_proportion - null_proportion)
    numerator = z_alpha * math.sqrt(null_proportion * (1.0 - null_proportion)) + z_power * math.sqrt(expected_proportion * (1.0 - expected_proportion))
    required = math.ceil((numerator / difference) ** 2)
    row = {"null_proportion": null_proportion, "expected_proportion": expected_proportion, "absolute_difference": difference, "alpha": alpha, "target_power": target_power, "required_sample_size": required}
    return ResultBundle(analysis_type="power.one_sample_proportion", engine_version=ENGINE_VERSION, input_digest=input_digest(row), parameters={"method": "normal_approximation_one_sample_proportion", "alternative": "two_sided"}, tables={"plan": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics=row, assumptions=("Each opportunity produces an independent binary outcome.", "The normal approximation is adequate for the target and expected defect rates."), warnings=("This is a prospective planning calculation; use an exact or continuity-corrected design for rare events when required by the protocol.",), provenance=(NIST_POWER_SOURCE,))


def paired_mean_sample_size(*, difference: float, difference_standard_deviation: float, alpha: float = 0.05, target_power: float = 0.8) -> ResultBundle:
    """Estimate required matched pairs for a two-sided paired mean comparison."""
    if difference <= 0 or difference_standard_deviation <= 0:
        raise AnalysisInputError("invalid_effect_inputs", "Difference and paired-difference standard deviation must be positive.", "difference")
    if not 0.001 <= alpha <= 0.5 or not 0.5 < target_power < 0.999:
        raise AnalysisInputError("invalid_power_inputs", "Use valid alpha and target power above 0.5.", "target_power")
    effect_size = difference / difference_standard_deviation
    z_alpha = _normal_quantile(1 - alpha / 2.0)
    z_power = _normal_quantile(target_power)
    required_pairs = math.ceil(((z_alpha + z_power) / effect_size) ** 2)
    row = {"difference": difference, "difference_standard_deviation": difference_standard_deviation, "paired_effect_size": effect_size, "alpha": alpha, "target_power": target_power, "required_pairs": required_pairs}
    return ResultBundle(analysis_type="power.paired_mean", engine_version=ENGINE_VERSION, input_digest=input_digest(row), parameters={"method": "normal_approximation_paired_mean", "alternative": "two_sided"}, tables={"plan": {"columns": list(row), "rows": [row]}}, plots={}, diagnostics=row, assumptions=("Each before/after pair belongs to the same unit and pairs are independent of each other.", "The paired differences have a planning standard deviation suitable for a normal approximation."), warnings=("This is a prospective planning calculation; estimate the standard deviation from paired pilot data, not separate marginal standard deviations.",), provenance=(NIST_POWER_SOURCE,))
