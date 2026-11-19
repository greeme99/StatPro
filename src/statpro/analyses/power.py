"""Prospective balanced two-sample sample-size planning."""
from __future__ import annotations
import math
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_POWER_SOURCE = ProvenanceSource(title="NIST/SEMATECH Sample Size and Power", url="https://www.itl.nist.gov/div898/handbook/prc/section2/prc222.htm")

def _normal_quantile(probability: float) -> float:
    if not 0.0 < probability < 1.0: raise AnalysisInputError("invalid_probability", "Probability must be strictly between zero and one.", "probability")
    low, high = -10.0, 10.0
    for _ in range(100):
        mid = (low + high) / 2.0
        if 0.5 * math.erfc(-mid / math.sqrt(2.0)) < probability: low = mid
        else: high = mid
    return (low + high) / 2.0

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
