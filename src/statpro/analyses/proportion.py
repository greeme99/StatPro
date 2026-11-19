"""One-sample proportion inference for defect-rate decisions."""
from __future__ import annotations
import math
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_PROPORTION_SOURCE = ProvenanceSource(title="NIST/SEMATECH Proportion Confidence Interval", url="https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm")

def _z(probability: float) -> float:
    low, high = -10.0, 10.0
    for _ in range(100):
        middle = (low + high) / 2
        if .5 * math.erfc(-middle / math.sqrt(2)) < probability: low = middle
        else: high = middle
    return (low + high) / 2

def one_sample_proportion_test(*, defects: int, opportunities: int, target: float, alpha: float = .05) -> ResultBundle:
    if opportunities <= 0 or defects < 0 or defects > opportunities or not 0 < target < 1 or not .001 <= alpha <= .5: raise AnalysisInputError("invalid_proportion_input", "Use valid defect count, opportunities, target rate, and alpha.", "defects")
    observed = defects / opportunities; standard_error = math.sqrt(target * (1 - target) / opportunities)
    z_value = (observed - target) / standard_error; p_value = math.erfc(abs(z_value) / math.sqrt(2)); critical = _z(1 - alpha / 2); denominator = 1 + critical**2 / opportunities; center = (observed + critical**2 / (2 * opportunities)) / denominator; half = critical * math.sqrt(observed * (1 - observed) / opportunities + critical**2 / (4 * opportunities**2)) / denominator
    row = {"defects": defects, "opportunities": opportunities, "observed_proportion": observed, "target_proportion": target, "z_value": z_value, "p_value": p_value, "wilson_lower": center-half, "wilson_upper": center+half, "significant": p_value <= alpha}
    return ResultBundle(analysis_type="hypothesis.one_sample_proportion", engine_version=ENGINE_VERSION, input_digest=input_digest({**row, "alpha":alpha}), parameters={"method":"one_sample_proportion_normal_test","alpha":alpha,"alternative":"two_sided"}, tables={"test":{"columns":list(row),"rows":[row]}}, plots={}, diagnostics=row, assumptions=("Each opportunity has a binary defect outcome and observations are independent.",), warnings=("Small expected counts can make the normal test approximation unreliable; interpret with the Wilson interval.",), provenance=(NIST_PROPORTION_SOURCE,))

def two_sample_proportion_test(*, defects_a: int, opportunities_a: int, defects_b: int, opportunities_b: int, alpha: float = .05) -> ResultBundle:
    """Two-sided pooled z test plus an unpooled interval for a proportion difference."""
    inputs = (defects_a, opportunities_a, defects_b, opportunities_b)
    if any(not isinstance(value, int) for value in inputs) or opportunities_a <= 0 or opportunities_b <= 0 or defects_a < 0 or defects_b < 0 or defects_a > opportunities_a or defects_b > opportunities_b or not .001 <= alpha <= .5: raise AnalysisInputError("invalid_two_proportion_input", "Use valid defect counts, opportunities, and alpha.", "defects_a")
    p_a, p_b = defects_a / opportunities_a, defects_b / opportunities_b; difference = p_a - p_b; pooled = (defects_a + defects_b) / (opportunities_a + opportunities_b); pooled_se = math.sqrt(pooled * (1 - pooled) * (1 / opportunities_a + 1 / opportunities_b))
    if pooled_se == 0: raise AnalysisInputError("zero_standard_error", "At least one defect and one non-defect are required across both groups.", "defects_a")
    z_value = difference / pooled_se; p_value = math.erfc(abs(z_value) / math.sqrt(2)); critical = _z(1-alpha/2); unpooled_se = math.sqrt(p_a*(1-p_a)/opportunities_a+p_b*(1-p_b)/opportunities_b); row={"proportion_a":p_a,"proportion_b":p_b,"difference":difference,"z_value":z_value,"p_value":p_value,"confidence_interval_lower":difference-critical*unpooled_se,"confidence_interval_upper":difference+critical*unpooled_se,"significant":p_value<=alpha}
    return ResultBundle(analysis_type="hypothesis.two_sample_proportion", engine_version=ENGINE_VERSION, input_digest=input_digest({"defects_a":defects_a,"opportunities_a":opportunities_a,"defects_b":defects_b,"opportunities_b":opportunities_b,"alpha":alpha}), parameters={"method":"two_proportion_pooled_z_test","alpha":alpha,"alternative":"two_sided"}, tables={"test":{"columns":list(row),"rows":[row]}}, plots={}, diagnostics=row, assumptions=("Groups are independent and each opportunity has a binary outcome.",), warnings=("Review expected defect and non-defect counts before relying on the normal approximation.",), provenance=(NIST_PROPORTION_SOURCE,))
