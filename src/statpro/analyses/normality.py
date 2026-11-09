"""Transparent large-sample normality diagnostics."""

from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import fmean

from statpro.analyses.common import finite_values
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_JARQUE_BERA_SOURCE = ProvenanceSource(
    title="NIST Dataplot Jarque-Bera Test",
    url="https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/jarqbera.htm",
)


def jarque_bera_normality(values: Sequence[float], *, alpha: float = 0.05) -> ResultBundle:
    """Return a Jarque-Bera skewness/kurtosis diagnostic.

    The p-value is the chi-square (two degrees of freedom) asymptotic survival
    probability.  It is deliberately accompanied by a small-sample warning:
    this function must not present an asymptotic approximation as an exact
    finite-sample test.
    """
    observations = finite_values(values, "values")
    if len(observations) < 3:
        raise AnalysisInputError("insufficient_observations", "Jarque-Bera requires at least three observations.", "values")
    if not 0.0 < alpha < 1.0:
        raise AnalysisInputError("invalid_alpha", "alpha must be between zero and one.", "alpha")
    mean = fmean(observations)
    centered = [value - mean for value in observations]
    m2 = fmean(value ** 2 for value in centered)
    if m2 == 0.0:
        raise AnalysisInputError("zero_variation", "Normality is undefined when all observations are equal.", "values")
    skewness = fmean(value ** 3 for value in centered) / m2 ** 1.5
    kurtosis = fmean(value ** 4 for value in centered) / m2 ** 2
    statistic = len(observations) / 6.0 * (skewness ** 2 + (kurtosis - 3.0) ** 2 / 4.0)
    p_value = math.exp(-statistic / 2.0)  # chi-square survival function, df=2
    return ResultBundle(
        analysis_type="normality.jarque_bera",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest({"values": observations, "alpha": alpha}),
        parameters={"test": "jarque_bera", "alpha": alpha, "sample_size": len(observations)},
        tables={"normality": {"columns": ["n", "skewness", "kurtosis", "jb_statistic", "p_value"], "rows": [{"n": len(observations), "skewness": skewness, "kurtosis": kurtosis, "jb_statistic": statistic, "p_value": p_value}]}},
        plots={},
        diagnostics={"reject_normality": p_value < alpha, "p_value": p_value, "asymptotic_chi_square_df": 2},
        assumptions=("Observations are independent.",),
        warnings=(
            (
                "The chi-square approximation is intended for large samples; "
                "NIST notes small samples need simulated critical values.",
            )
            if len(observations) < 2000
            else ()
        ),
        provenance=(NIST_JARQUE_BERA_SOURCE,),
    )
