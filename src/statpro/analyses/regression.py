"""Small, explicit ordinary least squares regression ResultBundles."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from statistics import fmean

from statpro.analyses.common import f_survival, finite_values, invert_matrix
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_LINEAR_LEAST_SQUARES_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH Linear Least Squares Regression",
    url="https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd141.htm",
)
NIST_LEAST_SQUARES_GLOSSARY_SOURCE = ProvenanceSource(
    title="NIST StRD Linear Least Squares Regression Glossary",
    url="https://www.itl.nist.gov/div898/strd/lls/data/LINKS/c-NoInt2.shtml",
)


def linear_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    alpha: float = 0.05,
) -> ResultBundle:
    """Fit an intercept-inclusive multiple linear OLS model.

    Weighted, robust, logistic, and automatic-selection models are separate
    methods and are not silently substituted here.
    """

    values = finite_values(response, "response")
    if not predictors:
        raise AnalysisInputError("missing_predictors", "At least one predictor is required.", "predictors")
    normalized_name = response_name.strip()
    if not normalized_name:
        raise AnalysisInputError("empty_response_name", "Response name cannot be empty.", "response_name")
    normalized_alpha = finite_values([alpha], "alpha")[0]
    if not 0.001 <= normalized_alpha <= 0.5:
        raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")

    predictor_names = list(predictors)
    if len(predictor_names) > 20:
        raise AnalysisInputError("too_many_predictors", "At most 20 predictors are supported.", "predictors")
    if any(not name.strip() for name in predictor_names):
        raise AnalysisInputError("empty_predictor_name", "Predictor names cannot be empty.", "predictors")
    normalized_predictors = {
        name: finite_values(column, f"predictors.{name}")
        for name, column in predictors.items()
    }
    sample_size = len(values)
    if any(len(column) != sample_size for column in normalized_predictors.values()):
        raise AnalysisInputError(
            "predictor_length_mismatch",
            "Every predictor must have the same number of observations as the response.",
            "predictors",
        )
    parameter_count = len(predictor_names) + 1
    residual_df = sample_size - parameter_count
    if residual_df < 1:
        raise AnalysisInputError(
            "insufficient_observations",
            "OLS requires more observations than fitted parameters.",
            "response",
        )

    matrix = [
        [1.0, *(normalized_predictors[name][index] for name in predictor_names)]
        for index in range(sample_size)
    ]
    cross_product = [
        [sum(row[left] * row[right] for row in matrix) for right in range(parameter_count)]
        for left in range(parameter_count)
    ]
    inverse = invert_matrix(cross_product, field="predictors")
    cross_response = [
        sum(row[column] * value for row, value in zip(matrix, values, strict=True))
        for column in range(parameter_count)
    ]
    coefficients = [
        sum(inverse[row][column] * cross_response[column] for column in range(parameter_count))
        for row in range(parameter_count)
    ]
    fitted = [
        sum(value * coefficient for value, coefficient in zip(row, coefficients, strict=True))
        for row in matrix
    ]
    residuals = [actual - prediction for actual, prediction in zip(values, fitted, strict=True)]
    response_mean = fmean(values)
    total_ss = sum((value - response_mean) ** 2 for value in values)
    residual_ss = sum(residual * residual for residual in residuals)
    model_ss = max(0.0, total_ss - residual_ss)
    model_df = parameter_count - 1
    residual_ms = residual_ss / residual_df
    model_ms = model_ss / model_df
    model_f = model_ms / residual_ms if residual_ms > 0.0 else None
    model_p = f_survival(model_f, model_df, residual_df)
    r_squared = 1.0 - residual_ss / total_ss if total_ss > 0.0 else None
    adjusted_r_squared = (
        1.0 - (1.0 - r_squared) * (sample_size - 1) / residual_df
        if r_squared is not None else None
    )

    terms = ["Intercept", *predictor_names]
    coefficient_rows: list[dict[str, float | str | bool | None]] = []
    for index, (term, coefficient) in enumerate(zip(terms, coefficients, strict=True)):
        standard_error = math.sqrt(max(0.0, residual_ms * inverse[index][index]))
        t_value = coefficient / standard_error if standard_error > 0.0 else None
        p_value = f_survival(t_value * t_value, 1, residual_df) if t_value is not None else None
        coefficient_rows.append({
            "term": term, "coefficient": coefficient, "standard_error": standard_error,
            "t_value": t_value, "p_value": p_value,
            "significant": p_value <= normalized_alpha if p_value is not None else False,
        })
    fitted_rows = []
    for index, (actual, prediction, residual) in enumerate(zip(values, fitted, residuals, strict=True)):
        leverage = sum(
            matrix[index][left] * inverse[left][right] * matrix[index][right]
            for left in range(parameter_count) for right in range(parameter_count)
        )
        fitted_rows.append({
            "observation": index + 1, "actual": actual, "fitted": prediction,
            "residual": residual, "leverage": leverage,
        })
    warnings = [
        "OLS estimates and inferential p-values assume independent errors with constant variance; inspect residuals before using the model operationally.",
        "Normal equations can be ill-conditioned for poorly scaled or collinear predictors; singular designs are rejected but near-singularity still needs engineering review.",
    ]
    if residual_ms == 0.0:
        warnings.append("Residual variance is zero; F and coefficient t/p statistics are not reported as exact significance claims.")
    if sample_size < 20:
        warnings.append("Small sample size: coefficient and model inference can be unstable.")
    return ResultBundle(
        analysis_type="regression.linear_ols",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest({"response": values, "predictors": normalized_predictors, "response_name": normalized_name, "alpha": normalized_alpha}),
        parameters={"response_name": normalized_name, "predictor_names": predictor_names, "alpha": normalized_alpha, "sample_size": sample_size, "parameter_count": parameter_count, "intercept": True},
        tables={
            "coefficients": {"columns": ["term", "coefficient", "standard_error", "t_value", "p_value", "significant"], "rows": coefficient_rows},
            "anova": {"columns": ["source", "degrees_of_freedom", "sum_squares", "mean_square", "f_value", "p_value"], "rows": [
                {"source": "Model", "degrees_of_freedom": model_df, "sum_squares": model_ss, "mean_square": model_ms, "f_value": model_f, "p_value": model_p},
                {"source": "Error", "degrees_of_freedom": residual_df, "sum_squares": residual_ss, "mean_square": residual_ms, "f_value": None, "p_value": None},
                {"source": "Total", "degrees_of_freedom": sample_size - 1, "sum_squares": total_ss, "mean_square": None, "f_value": None, "p_value": None},
            ]},
            "fitted_values": {"columns": ["observation", "actual", "fitted", "residual", "leverage"], "rows": fitted_rows},
        },
        plots={},
        diagnostics={"r_squared": r_squared, "adjusted_r_squared": adjusted_r_squared, "residual_standard_error": math.sqrt(residual_ms), "residual_degrees_of_freedom": residual_df, "model_f_statistic": model_f, "model_p_value": model_p},
        assumptions=(
            "The response is continuous and observations are aligned by row.",
            "Errors are independent with approximately constant variance.",
            "Coefficient and model inference additionally use the usual normal-error approximation.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE, NIST_LEAST_SQUARES_GLOSSARY_SOURCE),
    )
